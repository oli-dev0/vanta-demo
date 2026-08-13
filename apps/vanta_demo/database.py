import uuid
from pathlib import Path

from django.conf import settings
from django.db import connections

from .context import get_workspace_alias


CONTROL_APPS = frozenset({'sessions', 'vanta_demo'})
WORKSPACE_APPS = frozenset({
    'admin',
    'auth',
    'contenttypes',
    'demo_content',
    'demo_projects',
    'demo_newsletter',
    'demo_status',
    'demo_contact',
})
DENIED_DATABASE_ALIAS = 'vanta_demo_workspace_required'
WORKSPACE_ALIAS_PREFIX = 'vanta_workspace_'
SEED_DATABASE_ALIAS = 'vanta_demo_seed'


class UnsafeWorkspacePath(ValueError):
    pass


def workspace_alias(workspace_id):
    return f'{WORKSPACE_ALIAS_PREFIX}{uuid.UUID(str(workspace_id)).hex}'


def workspace_path(workspace_id):
    root = Path(settings.VANTA_DEMO_WORKSPACE_ROOT).resolve()
    candidate = (root / f'{uuid.UUID(str(workspace_id))}.sqlite3').resolve(strict=False)
    if candidate.parent != root:
        raise UnsafeWorkspacePath('Workspace path escaped its configured root.')
    return candidate


def workspace_temp_path(workspace_id):
    path = workspace_path(workspace_id)
    return path.with_suffix('.sqlite3.tmp')


def sqlite_database_config(path):
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(path),
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
        'OPTIONS': {'timeout': settings.VANTA_DEMO_SQLITE_TIMEOUT_SECONDS},
        'TIME_ZONE': None,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'MIGRATE': True,
            'MIRROR': None,
            'NAME': None,
        },
    }


def register_workspace_database(workspace_id, path=None):
    alias = workspace_alias(workspace_id)
    expected_path = workspace_path(workspace_id)
    resolved_path = Path(path or expected_path).resolve(strict=False)
    if resolved_path != expected_path:
        raise UnsafeWorkspacePath('Workspace database path did not match its derived path.')
    if alias not in connections.databases:
        connections.databases[alias] = sqlite_database_config(resolved_path)
    return alias


def register_seed_database(path):
    resolved_path = Path(path).resolve(strict=False)
    if SEED_DATABASE_ALIAS in connections.databases:
        connections[SEED_DATABASE_ALIAS].close()
        del connections[SEED_DATABASE_ALIAS]
    connections.databases[SEED_DATABASE_ALIAS] = sqlite_database_config(resolved_path)
    return SEED_DATABASE_ALIAS


def close_workspace_connection(alias):
    if alias in connections.databases:
        connections[alias].close()


class DemoWorkspaceRouter:
    def db_for_read(self, model, **hints):
        del hints
        app_label = model._meta.app_label
        if app_label in CONTROL_APPS:
            return 'default'
        if app_label in WORKSPACE_APPS:
            return get_workspace_alias() or DENIED_DATABASE_ALIAS
        return DENIED_DATABASE_ALIAS

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        del hints
        app_labels = {obj1._meta.app_label, obj2._meta.app_label}
        if app_labels <= CONTROL_APPS:
            return obj1._state.db == obj2._state.db == 'default'
        if app_labels <= WORKSPACE_APPS:
            alias = get_workspace_alias()
            return bool(alias and obj1._state.db == obj2._state.db == alias)
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        del model_name, hints
        if db == 'default':
            return app_label in CONTROL_APPS
        if db == SEED_DATABASE_ALIAS or db.startswith(WORKSPACE_ALIAS_PREFIX):
            return app_label in WORKSPACE_APPS
        return False
