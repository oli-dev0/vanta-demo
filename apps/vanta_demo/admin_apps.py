from django.contrib.admin.apps import SimpleAdminConfig


class DemoAdminConfig(SimpleAdminConfig):
    default_site = 'apps.vanta_demo.admin.DemoAdminSite'
