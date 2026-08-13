from django.contrib.auth import get_user_model

from .context import get_workspace_alias


class DemoWorkspaceBackend:
    def authenticate(self, request, **credentials):
        del request, credentials
        return None

    def get_user(self, user_id):
        alias = get_workspace_alias()
        if not alias:
            return None
        user_model = get_user_model()
        try:
            return user_model._default_manager.using(alias).get(pk=user_id)
        except (user_model.DoesNotExist, ValueError):
            return None

    def user_can_authenticate(self, user):
        return user.is_active
