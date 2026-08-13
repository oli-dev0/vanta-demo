import shutil
import tempfile
import unittest
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper

from apps.vanta_demo.models import DemoCapacityLock


REAL_ENSURE_CONNECTION = BaseDatabaseWrapper.ensure_connection


class DemoFilesystemMixin:
    databases = {'default'}

    @classmethod
    def setUpClass(cls):
        if not hasattr(settings, 'VANTA_DEMO_SEED_PATH'):
            raise unittest.SkipTest('The isolated Vanta demo settings are not active.')
        super().setUpClass()
        cls._testcase_ensure_connection = BaseDatabaseWrapper.ensure_connection
        BaseDatabaseWrapper.ensure_connection = REAL_ENSURE_CONNECTION
        cls._temporary_directory = tempfile.TemporaryDirectory(prefix='vanta-demo-tests-')
        root = Path(cls._temporary_directory.name)
        workspace_root = root / 'workspaces'
        workspace_root.mkdir(mode=0o700)
        static_root = root / 'staticfiles'
        static_root.mkdir()
        seed_path = root / 'seed.sqlite3'
        shutil.copyfile(settings.VANTA_DEMO_SEED_PATH, seed_path)
        seed_path.chmod(0o444)
        cls._original_demo_settings = {
            'VANTA_DEMO_WORKSPACE_ROOT': settings.VANTA_DEMO_WORKSPACE_ROOT,
            'VANTA_DEMO_SEED_PATH': settings.VANTA_DEMO_SEED_PATH,
            'VANTA_DEMO_HASH_SECRET': settings.VANTA_DEMO_HASH_SECRET,
            'STATIC_ROOT': settings.STATIC_ROOT,
        }
        settings.VANTA_DEMO_WORKSPACE_ROOT = workspace_root
        settings.VANTA_DEMO_SEED_PATH = seed_path
        settings.VANTA_DEMO_HASH_SECRET = 'test-hash-secret'
        settings.STATIC_ROOT = static_root

    @classmethod
    def tearDownClass(cls):
        for name, value in cls._original_demo_settings.items():
            setattr(settings, name, value)
        cls._temporary_directory.cleanup()
        for alias in list(connections):
            if alias == 'default':
                continue
            connections[alias].close()
            del connections[alias]
            connections.databases.pop(alias, None)
        BaseDatabaseWrapper.ensure_connection = cls._testcase_ensure_connection
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        DemoCapacityLock.objects.get_or_create(pk=1)

    def start_demo(self, client=None):
        client = client or self.client
        client.get('/')
        return client.post('/start/', data='', content_type='application/x-www-form-urlencoded')
