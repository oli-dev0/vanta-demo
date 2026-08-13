from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VantaDemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vanta_demo'
    label = 'vanta_demo'
    verbose_name = _('Vanta demo control')

    def ready(self):
        from . import checks  # noqa: F401
