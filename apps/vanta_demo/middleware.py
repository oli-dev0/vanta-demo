from django.conf import settings
from django.db import OperationalError
from django.shortcuts import redirect
from django.utils import timezone

from .context import workspace_database
from .database import close_workspace_connection, register_workspace_database, workspace_path
from .models import DemoWorkspace
from .services.workspaces import (
    BROWSER_SESSION_KEY,
    RESET_PREFERENCES_SESSION_KEY,
    WORKSPACE_SESSION_KEY,
    detach_workspace_session,
    refresh_workspace_activity,
    validate_workspace_file,
)


class DemoWorkspaceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.content_type and request.content_type.startswith('multipart/'):
            from .views import state_response

            return state_response(request, 'unavailable', status=415)

        workspace = self._load_workspace(request)
        if workspace is None:
            if request.path.startswith('/admin/'):
                if getattr(request, 'vanta_demo_expired', False):
                    return redirect('vanta_demo:expired')
                return redirect('/?state=start')
            return self.get_response(request)

        alias = register_workspace_database(workspace.id)
        try:
            with workspace_database(alias):
                if request.path.startswith('/admin/'):
                    request.vanta_demo_reset_preferences = bool(
                        request.session.pop(RESET_PREFERENCES_SESSION_KEY, False)
                    )
                response = self._workspace_response(request, alias)
                if request.path.startswith('/admin/'):
                    refresh_workspace_activity(workspace)
                    response.headers['Cache-Control'] = 'no-store, private'
                return response
        finally:
            close_workspace_connection(alias)

    def _workspace_response(self, request, alias):
        attempts = 2 if request.method in {'GET', 'HEAD'} else 1
        for attempt in range(attempts):
            try:
                return self.get_response(request)
            except OperationalError as error:
                busy = 'locked' in str(error).lower() or 'busy' in str(error).lower()
                if not busy:
                    raise
                close_workspace_connection(alias)
                if attempt + 1 < attempts:
                    continue
                from .views import state_response

                return state_response(request, 'unavailable', status=503)
        raise AssertionError('The workspace response retry loop did not return.')

    def _load_workspace(self, request):
        workspace_id = request.session.get(WORKSPACE_SESSION_KEY)
        browser_id = request.session.get(BROWSER_SESSION_KEY)
        if not workspace_id or not browser_id:
            return None
        try:
            workspace = DemoWorkspace.objects.using('default').get(
                pk=workspace_id,
                browser_id=browser_id,
            )
        except (DemoWorkspace.DoesNotExist, ValueError):
            detach_workspace_session(request)
            return None

        now = timezone.now()
        path = workspace_path(workspace.id)
        active = workspace.is_active(seed_version=settings.VANTA_DEMO_SEED_VERSION, at=now)
        valid_file = path.is_file() and validate_workspace_file(path)
        if active and valid_file:
            request.demo_workspace = workspace
            return workspace

        status = DemoWorkspace.Status.EXPIRED
        failure_code = ''
        if active and not valid_file:
            status = DemoWorkspace.Status.FAILED
            failure_code = 'workspace_invalid'
        DemoWorkspace.objects.using('default').filter(pk=workspace.pk).update(
            status=status,
            retired_at=now,
            failure_code=failure_code,
        )
        detach_workspace_session(request)
        if request.path.startswith('/admin/'):
            request.vanta_demo_expired = True
        return None
