import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, connections, transaction
from django.test import TransactionTestCase
from django.utils.connection import ConnectionDoesNotExist
from django.utils import timezone

from apps.demo_content.models import BlogPost
from apps.demo_newsletter.models import Campaign

from apps.vanta_demo.backends import DemoWorkspaceBackend
from apps.vanta_demo.context import workspace_database
from apps.vanta_demo.database import (
    DENIED_DATABASE_ALIAS,
    DemoWorkspaceRouter,
    UnsafeWorkspacePath,
    register_workspace_database,
    workspace_path,
)
from apps.vanta_demo.models import DemoCapacityLock, DemoWorkspace
from .base import DemoFilesystemMixin


class DemoWorkspaceModelTests(DemoFilesystemMixin, TransactionTestCase):
    def test_capacity_lock_uses_the_singleton_row(self):
        self.assertEqual(list(DemoCapacityLock.objects.values_list('pk', flat=True)), [1])

    def _workspace(self, browser_id, status=DemoWorkspace.Status.ACTIVE):
        now = timezone.now()
        return DemoWorkspace.objects.create(
            browser_id=browser_id,
            status=status,
            seed_version='0.22.2-1',
            expires_at=now + timedelta(hours=2),
            last_activity_at=now,
        )

    def test_only_one_live_workspace_is_allowed_per_browser(self):
        browser_id = uuid.uuid4()
        self._workspace(browser_id)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._workspace(browser_id, DemoWorkspace.Status.CREATING)

    def test_retired_workspace_does_not_block_replacement(self):
        browser_id = uuid.uuid4()
        first = self._workspace(browser_id, DemoWorkspace.Status.RETIRED)
        replacement = self._workspace(browser_id)
        self.assertNotEqual(first.pk, replacement.pk)

    def test_active_state_requires_current_seed_and_future_expiry(self):
        workspace = self._workspace(uuid.uuid4())
        self.assertTrue(workspace.is_active(seed_version='0.22.2-1'))
        self.assertFalse(workspace.is_active(seed_version='0.15.2-1'))
        workspace.expires_at = timezone.now() - timedelta(seconds=1)
        self.assertFalse(workspace.is_active(seed_version='0.22.2-1'))


class DemoDatabaseBoundaryTests(DemoFilesystemMixin, TransactionTestCase):
    def test_workspace_models_are_denied_without_request_context(self):
        router = DemoWorkspaceRouter()
        self.assertEqual(router.db_for_read(BlogPost), DENIED_DATABASE_ALIAS)
        self.assertEqual(router.db_for_read(Campaign), DENIED_DATABASE_ALIAS)
        with self.assertRaises(ConnectionDoesNotExist):
            BlogPost.objects.count()

    def test_control_models_always_route_to_default(self):
        router = DemoWorkspaceRouter()
        self.assertEqual(router.db_for_read(DemoWorkspace), 'default')
        self.assertTrue(router.allow_migrate('default', 'vanta_demo'))
        self.assertFalse(router.allow_migrate('default', 'auth'))

    def test_registered_workspace_alias_routes_workspace_models(self):
        workspace_id = uuid.uuid4()
        path = workspace_path(workspace_id)
        path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())
        alias = register_workspace_database(workspace_id)
        try:
            with workspace_database(alias):
                self.assertEqual(DemoWorkspaceRouter().db_for_read(BlogPost), alias)
                self.assertGreater(BlogPost.objects.count(), 10)
        finally:
            connections[alias].close()

    def test_register_rejects_a_non_derived_path(self):
        with self.assertRaises(UnsafeWorkspacePath):
            register_workspace_database(uuid.uuid4(), '/tmp/not-the-derived-workspace.sqlite3')

    def test_backend_rejects_credentials_and_requires_workspace_context(self):
        backend = DemoWorkspaceBackend()
        self.assertIsNone(
            backend.authenticate(None, username='demo-admin', password='anything')
        )
        self.assertIsNone(backend.get_user(1))

        workspace_id = uuid.uuid4()
        path = workspace_path(workspace_id)
        path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())
        alias = register_workspace_database(workspace_id)
        try:
            with workspace_database(alias):
                self.assertEqual(backend.get_user(1).username, 'demo-admin')
        finally:
            connections[alias].close()

        self.assertIsNone(backend.get_user(1))
