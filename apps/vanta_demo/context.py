from contextlib import contextmanager
from contextvars import ContextVar


_workspace_alias = ContextVar('vanta_demo_workspace_alias', default=None)


def get_workspace_alias():
    return _workspace_alias.get()


@contextmanager
def workspace_database(alias):
    token = _workspace_alias.set(alias)
    try:
        yield alias
    finally:
        _workspace_alias.reset(token)
