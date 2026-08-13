import os


if os.environ.get('DJANGO_SETTINGS_MODULE') in {
    'config.settings.local',
    'config.settings.production',
    'config.settings.demo',
    'config.settings.demo_seed',
}:
    pass
else:
    from .local import *  # noqa: F403

