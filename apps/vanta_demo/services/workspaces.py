import hashlib
import hmac
import ipaddress
import logging
import os
import secrets
import shutil
import sqlite3
import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model, login
from django.db import IntegrityError, transaction
from django.utils import timezone

from ..context import workspace_database
from ..database import (
    close_workspace_connection,
    register_workspace_database,
    workspace_path,
    workspace_temp_path,
)
from ..models import DemoCapacityLock, DemoThrottleBucket, DemoWorkspace


logger = logging.getLogger(__name__)

BROWSER_SESSION_KEY = 'vanta_demo_browser_id'
WORKSPACE_SESSION_KEY = 'vanta_demo_workspace_id'
START_MARKER_SESSION_KEY = 'vanta_demo_start_marker'
RESET_PREFERENCES_SESSION_KEY = 'vanta_demo_reset_preferences'
DEMO_ADMIN_USERNAME = 'demo-admin'
DEMO_BACKEND = 'apps.vanta_demo.backends.DemoWorkspaceBackend'


def seed_activity_timestamp(now, index):
    """Return a stable day-relative timestamp for seeded activity entries."""
    local_now = timezone.localtime(now)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    if index < 6:
        return max(today_start, local_now - timedelta(minutes=(index + 1) * 5))

    yesterday_start = today_start - timedelta(days=1)
    return yesterday_start + timedelta(hours=10, minutes=(index - 6) * 5)


class DemoWorkspaceError(RuntimeError):
    pass


class DemoCookiesRequired(DemoWorkspaceError):
    pass


class DemoRateLimited(DemoWorkspaceError):
    def __init__(self, retry_after):
        self.retry_after = max(1, int(retry_after))
        super().__init__('Workspace start rate exceeded.')


class DemoCapacityReached(DemoWorkspaceError):
    pass


class DemoWorkspaceUnavailable(DemoWorkspaceError):
    pass


def ensure_browser_session(request):
    browser_id = request.session.get(BROWSER_SESSION_KEY)
    try:
        browser_id = uuid.UUID(str(browser_id))
    except (TypeError, ValueError, AttributeError):
        browser_id = uuid.uuid4()
        request.session[BROWSER_SESSION_KEY] = str(browser_id)
    request.session.modified = True
    return browser_id


def issue_start_marker(request):
    request.session[START_MARKER_SESSION_KEY] = secrets.token_urlsafe(24)
    request.session.modified = True


def _require_start_marker(request):
    cookie_name = settings.SESSION_COOKIE_NAME
    marker = request.session.pop(START_MARKER_SESSION_KEY, None)
    if not request.COOKIES.get(cookie_name) or not marker:
        raise DemoCookiesRequired


def detach_workspace_session(request):
    for key in (WORKSPACE_SESSION_KEY, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY):
        request.session.pop(key, None)
    request.session.modified = True


def _normalized_client_address(request):
    header = settings.VANTA_DEMO_TRUSTED_IP_HEADER
    raw_address = request.META.get(header) or request.META.get('REMOTE_ADDR', '')
    candidate = raw_address.split(',', 1)[0].strip()
    try:
        return ipaddress.ip_address(candidate).compressed
    except ValueError:
        return 'unknown'


def _client_key_hash(request):
    address = _normalized_client_address(request)
    return hmac.new(
        settings.VANTA_DEMO_HASH_SECRET.encode(),
        address.encode(),
        hashlib.sha256,
    ).hexdigest()


def consume_start_throttle(request, *, now=None):
    now = now or timezone.now()
    window_seconds = settings.VANTA_DEMO_START_WINDOW_SECONDS
    window_end = now + timedelta(seconds=window_seconds)
    key_hash = _client_key_hash(request)

    for attempt in range(2):
        try:
            with transaction.atomic(using='default'):
                bucket, created = (
                    DemoThrottleBucket.objects.using('default')
                    .select_for_update()
                    .get_or_create(
                        key_hash=key_hash,
                        action=DemoThrottleBucket.Action.WORKSPACE_START,
                        defaults={
                            'window_started_at': now,
                            'count': 0,
                            'expires_at': window_end,
                        },
                    )
                )
                if not created and bucket.expires_at <= now:
                    bucket.window_started_at = now
                    bucket.count = 0
                    bucket.expires_at = window_end
                if bucket.count >= settings.VANTA_DEMO_START_LIMIT:
                    retry_after = (bucket.expires_at - now).total_seconds()
                    raise DemoRateLimited(retry_after)
                bucket.count += 1
                bucket.save(
                    using='default',
                    update_fields=['window_started_at', 'count', 'expires_at'],
                )
            return
        except IntegrityError:
            if attempt:
                raise DemoWorkspaceUnavailable from None


def _expire_stale_capacity_rows(now):
    creating_before = now - timedelta(seconds=settings.VANTA_DEMO_CREATING_TIMEOUT_SECONDS)
    DemoWorkspace.objects.using('default').filter(
        status=DemoWorkspace.Status.CREATING,
        created_at__lte=creating_before,
    ).update(
        status=DemoWorkspace.Status.EXPIRED,
        retired_at=now,
        failure_code='creation_timeout',
    )
    DemoWorkspace.objects.using('default').filter(
        status=DemoWorkspace.Status.ACTIVE,
        expires_at__lte=now,
    ).update(status=DemoWorkspace.Status.EXPIRED, retired_at=now)


def reserve_workspace(browser_id, *, replacement=False, now=None):
    now = now or timezone.now()
    reservation_browser_id = uuid.uuid4() if replacement else browser_id
    expires_at = now + timedelta(seconds=settings.VANTA_DEMO_WORKSPACE_TTL_SECONDS)
    with transaction.atomic(using='default'):
        DemoCapacityLock.objects.using('default').get_or_create(pk=1)
        DemoCapacityLock.objects.using('default').select_for_update().get(pk=1)
        _expire_stale_capacity_rows(now)
        if not replacement and DemoWorkspace.objects.using('default').filter(
            browser_id=browser_id,
            status__in=[DemoWorkspace.Status.CREATING, DemoWorkspace.Status.ACTIVE],
        ).exists():
            raise DemoWorkspaceUnavailable
        live_count = DemoWorkspace.objects.using('default').filter(
            status__in=[DemoWorkspace.Status.CREATING, DemoWorkspace.Status.ACTIVE]
        ).count()
        if live_count >= settings.VANTA_DEMO_MAX_WORKSPACES:
            raise DemoCapacityReached
        return DemoWorkspace.objects.using('default').create(
            browser_id=reservation_browser_id,
            seed_version=settings.VANTA_DEMO_SEED_VERSION,
            expires_at=expires_at,
            last_activity_at=now,
        )


def validate_workspace_file(path):
    expected_tables = {
        'auth_user',
        'django_admin_log',
        'demo_content_blogpost',
        'demo_projects_project',
        'demo_newsletter_campaign',
        'demo_status_incident',
        'demo_contact_contactmessage',
    }
    uri = f'file:{Path(path).as_posix()}?mode=ro'
    try:
        with sqlite3.connect(uri, uri=True, timeout=2) as connection:
            result = connection.execute('PRAGMA quick_check').fetchone()
            if not result or result[0] != 'ok':
                return False
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            if not expected_tables <= tables:
                return False
            admin = connection.execute(
                'SELECT is_active, is_staff, is_superuser FROM auth_user WHERE username = ?',
                (DEMO_ADMIN_USERNAME,),
            ).fetchone()
    except (OSError, sqlite3.DatabaseError):
        return False
    return admin == (1, 1, 1)


def _remove_workspace_files(workspace_id):
    for path in (workspace_temp_path(workspace_id), workspace_path(workspace_id)):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning('Vanta demo workspace file cleanup failed category=file_remove')


def materialize_workspace(workspace):
    root = Path(settings.VANTA_DEMO_WORKSPACE_ROOT)
    seed_path = Path(settings.VANTA_DEMO_SEED_PATH)
    if not root.is_dir() or not seed_path.is_file() or not validate_workspace_file(seed_path):
        raise DemoWorkspaceUnavailable

    final_path = workspace_path(workspace.id)
    temp_path = workspace_temp_path(workspace.id)
    try:
        root.chmod(0o700)
        temp_path.unlink(missing_ok=True)
        shutil.copyfile(seed_path, temp_path)
        temp_path.chmod(0o600)
        os.replace(temp_path, final_path)
        final_path.chmod(0o600)
        _refresh_seed_activity(final_path)
        if not validate_workspace_file(final_path):
            raise DemoWorkspaceUnavailable
    except (OSError, sqlite3.DatabaseError, DemoWorkspaceUnavailable):
        _remove_workspace_files(workspace.id)
        raise DemoWorkspaceUnavailable from None
    return final_path


def _refresh_seed_activity(path, *, now=None):
    now = now or timezone.now()
    with sqlite3.connect(path, timeout=2) as connection:
        log_ids = connection.execute(
            'SELECT id FROM django_admin_log ORDER BY action_time DESC, id DESC'
        ).fetchall()
        connection.executemany(
            'UPDATE django_admin_log SET action_time = ? WHERE id = ?',
            [
                (seed_activity_timestamp(now, index), log_id)
                for index, (log_id,) in enumerate(log_ids)
            ],
        )


def _mark_failed(workspace, failure_code):
    DemoWorkspace.objects.using('default').filter(pk=workspace.pk).update(
        status=DemoWorkspace.Status.FAILED,
        retired_at=timezone.now(),
        failure_code=failure_code,
    )
    logger.warning('vanta_demo_workspace_failed failure_code=%s', failure_code)


def _activate_workspace(workspace):
    now = timezone.now()
    DemoWorkspace.objects.using('default').filter(pk=workspace.pk).update(
        status=DemoWorkspace.Status.ACTIVE,
        last_activity_at=now,
        expires_at=now + timedelta(seconds=settings.VANTA_DEMO_WORKSPACE_TTL_SECONDS),
        failure_code='',
    )
    workspace.status = DemoWorkspace.Status.ACTIVE


def sign_in_demo_admin(request, workspace):
    alias = register_workspace_database(workspace.id)
    try:
        with workspace_database(alias):
            user = get_user_model().objects.using(alias).get(username=DEMO_ADMIN_USERNAME)
            login(request, user, backend=DEMO_BACKEND)
    finally:
        close_workspace_connection(alias)


def _valid_session_workspace(request, browser_id, *, now=None):
    now = now or timezone.now()
    workspace_id = request.session.get(WORKSPACE_SESSION_KEY)
    workspace = None
    if workspace_id:
        try:
            workspace = DemoWorkspace.objects.using('default').get(
                pk=workspace_id,
                browser_id=browser_id,
            )
        except (DemoWorkspace.DoesNotExist, ValueError):
            detach_workspace_session(request)
    if workspace is None:
        workspace = (
            DemoWorkspace.objects.using('default')
            .filter(browser_id=browser_id, status=DemoWorkspace.Status.ACTIVE)
            .order_by('-created_at')
            .first()
        )
        if workspace:
            request.session[WORKSPACE_SESSION_KEY] = str(workspace.pk)
    if workspace is None:
        return None
    if not workspace.is_active(seed_version=settings.VANTA_DEMO_SEED_VERSION, at=now):
        DemoWorkspace.objects.using('default').filter(pk=workspace.pk).update(
            status=DemoWorkspace.Status.EXPIRED,
            retired_at=now,
        )
        detach_workspace_session(request)
        return None
    path = workspace_path(workspace.id)
    if not path.is_file() or not validate_workspace_file(path):
        DemoWorkspace.objects.using('default').filter(pk=workspace.pk).update(
            status=DemoWorkspace.Status.FAILED,
            retired_at=now,
            failure_code='workspace_invalid',
        )
        detach_workspace_session(request)
        return None
    return workspace


def refresh_workspace_activity(workspace, *, force=False, now=None):
    now = now or timezone.now()
    refresh_before = now - timedelta(seconds=settings.VANTA_DEMO_ACTIVITY_REFRESH_SECONDS)
    if not force and workspace.last_activity_at > refresh_before:
        return
    expires_at = now + timedelta(seconds=settings.VANTA_DEMO_WORKSPACE_TTL_SECONDS)
    DemoWorkspace.objects.using('default').filter(
        pk=workspace.pk,
        status=DemoWorkspace.Status.ACTIVE,
        last_activity_at__lte=refresh_before,
    ).update(last_activity_at=now, expires_at=expires_at)


def _create_workspace(browser_id, *, replacement=False):
    workspace = reserve_workspace(browser_id, replacement=replacement)
    try:
        materialize_workspace(workspace)
        _activate_workspace(workspace)
    except (DemoCapacityReached, DemoWorkspaceUnavailable):
        _mark_failed(workspace, 'workspace_create')
        _remove_workspace_files(workspace.id)
        raise
    except (IntegrityError, OSError):
        _mark_failed(workspace, 'workspace_create')
        _remove_workspace_files(workspace.id)
        raise DemoWorkspaceUnavailable from None
    return workspace


def _restore_current_workspace_session(request, current, browser_id):
    if current:
        active = DemoWorkspace.objects.using('default').filter(
            pk=current.pk,
            browser_id=browser_id,
            status=DemoWorkspace.Status.ACTIVE,
        ).exists()
        if active and workspace_path(current.pk).is_file():
            request.session[WORKSPACE_SESSION_KEY] = str(current.pk)
            return
    detach_workspace_session(request)


def _finalize_reset_workspace(browser_id, current, replacement):
    now = timezone.now()
    with transaction.atomic(using='default'):
        DemoCapacityLock.objects.using('default').get_or_create(pk=1)
        DemoCapacityLock.objects.using('default').select_for_update().get(pk=1)
        replacement = DemoWorkspace.objects.using('default').select_for_update().get(
            pk=replacement.pk,
            status=DemoWorkspace.Status.ACTIVE,
        )
        assigned = (
            DemoWorkspace.objects.using('default')
            .select_for_update()
            .filter(
                browser_id=browser_id,
                status__in=[DemoWorkspace.Status.CREATING, DemoWorkspace.Status.ACTIVE],
            )
            .order_by('-created_at')
            .first()
        )

        if assigned and current and assigned.pk == current.pk:
            assigned.status = DemoWorkspace.Status.RETIRED
            assigned.retired_at = now
            assigned.save(using='default', update_fields=['status', 'retired_at'])
            assigned = None

        if assigned:
            if assigned.status == DemoWorkspace.Status.CREATING:
                raise DemoWorkspaceUnavailable
            replacement.status = DemoWorkspace.Status.RETIRED
            replacement.retired_at = now
            replacement.save(using='default', update_fields=['status', 'retired_at'])
            return assigned, replacement

        replacement.browser_id = browser_id
        replacement.save(using='default', update_fields=['browser_id'])
        return replacement, current


def start_or_resume_workspace(request):
    _require_start_marker(request)
    browser_id = ensure_browser_session(request)
    consume_start_throttle(request)
    workspace = _valid_session_workspace(request, browser_id)
    if workspace:
        refresh_workspace_activity(workspace, force=True)
        sign_in_demo_admin(request, workspace)
        return workspace

    workspace = _create_workspace(browser_id)
    request.session[WORKSPACE_SESSION_KEY] = str(workspace.id)
    try:
        sign_in_demo_admin(request, workspace)
    except Exception:
        detach_workspace_session(request)
        _mark_failed(workspace, 'admin_sign_in')
        _remove_workspace_files(workspace.id)
        raise DemoWorkspaceUnavailable from None
    return workspace


def reset_workspace(request):
    _require_start_marker(request)
    browser_id = ensure_browser_session(request)
    consume_start_throttle(request)
    current = _valid_session_workspace(request, browser_id)

    replacement = _create_workspace(browser_id, replacement=True)
    try:
        sign_in_demo_admin(request, replacement)
    except Exception:
        _restore_current_workspace_session(request, current, browser_id)
        _mark_failed(replacement, 'workspace_reset')
        _remove_workspace_files(replacement.id)
        raise DemoWorkspaceUnavailable from None

    try:
        workspace, discarded = _finalize_reset_workspace(browser_id, current, replacement)
    except (DemoWorkspace.DoesNotExist, DemoWorkspaceUnavailable, IntegrityError):
        _restore_current_workspace_session(request, current, browser_id)
        _mark_failed(replacement, 'workspace_reset')
        _remove_workspace_files(replacement.id)
        raise DemoWorkspaceUnavailable from None

    if discarded:
        _remove_workspace_files(discarded.id)
    if workspace.pk != replacement.pk:
        try:
            sign_in_demo_admin(request, workspace)
        except Exception:
            request.session[WORKSPACE_SESSION_KEY] = str(workspace.id)
            raise DemoWorkspaceUnavailable from None
    request.session[WORKSPACE_SESSION_KEY] = str(workspace.id)
    return workspace
