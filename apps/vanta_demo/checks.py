import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from django.conf import settings
from django.core.checks import Error, Tags, register


DEMO_CHECK_TAG = 'vanta_demo'
EXPECTED_THEME_VERSION = '0.23.0'
EXPECTED_SEED_VERSION = '0.23.0-1'


@register(DEMO_CHECK_TAG, Tags.security)
def check_demo_runtime(app_configs, **kwargs):
    del app_configs, kwargs
    if getattr(settings, 'VANTA_DEMO_SKIP_RUNTIME_CHECKS', False):
        return []

    errors = []
    if not settings.VANTA_DEMO_HASH_SECRET:
        errors.append(Error('VANTA_DEMO_HASH_SECRET is required.', id='vanta_demo.E001'))
    if settings.VANTA_DEMO_SEED_VERSION != EXPECTED_SEED_VERSION:
        errors.append(
            Error(
                f'VANTA_DEMO_SEED_VERSION must be {EXPECTED_SEED_VERSION}.',
                id='vanta_demo.E002',
            )
        )

    for name in (
        'VANTA_DEMO_WORKSPACE_TTL_SECONDS',
        'VANTA_DEMO_MAX_WORKSPACES',
        'VANTA_DEMO_START_LIMIT',
        'VANTA_DEMO_START_WINDOW_SECONDS',
    ):
        if getattr(settings, name) <= 0:
            errors.append(Error(f'{name} must be greater than zero.', id='vanta_demo.E003'))

    workspace_root = Path(settings.VANTA_DEMO_WORKSPACE_ROOT)
    if not workspace_root.is_dir() or not os.access(workspace_root, os.W_OK | os.X_OK):
        errors.append(
            Error('The Vanta demo workspace root must exist and be writable.', id='vanta_demo.E004')
        )

    seed_path = Path(settings.VANTA_DEMO_SEED_PATH)
    if not seed_path.is_file() or not os.access(seed_path, os.R_OK):
        errors.append(Error('The Vanta demo seed must exist and be readable.', id='vanta_demo.E005'))

    try:
        theme_version = version('vanta-admin')
    except PackageNotFoundError:
        theme_version = None
    if theme_version != EXPECTED_THEME_VERSION:
        errors.append(
            Error(
                f'vanta-admin {EXPECTED_THEME_VERSION} must be installed.',
                id='vanta_demo.E006',
            )
        )

    middleware = list(settings.MIDDLEWARE)
    try:
        session_index = middleware.index('django.contrib.sessions.middleware.SessionMiddleware')
        demo_index = middleware.index('apps.vanta_demo.middleware.DemoWorkspaceMiddleware')
        auth_index = middleware.index('django.contrib.auth.middleware.AuthenticationMiddleware')
    except ValueError:
        errors.append(Error('The Vanta demo middleware stack is incomplete.', id='vanta_demo.E007'))
    else:
        if not session_index < demo_index < auth_index:
            errors.append(
                Error(
                    'DemoWorkspaceMiddleware must run after sessions and before authentication.',
                    id='vanta_demo.E008',
                )
            )
    return errors
