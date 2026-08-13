import uuid
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.db import close_old_connections, connection, connections, transaction
from django.test import Client, RequestFactory, TransactionTestCase, override_settings
from django.utils import timezone

from apps.demo_content.models import BlogPost, BlogPostTranslation

from apps.vanta_demo.context import workspace_database
from apps.vanta_demo.database import register_workspace_database, workspace_path
from apps.vanta_demo.models import DemoThrottleBucket, DemoWorkspace
from apps.vanta_demo.services import (
    DemoCapacityReached,
    DemoRateLimited,
    DemoWorkspaceUnavailable,
)
from apps.vanta_demo.services.workspaces import (
    BROWSER_SESSION_KEY,
    WORKSPACE_SESSION_KEY,
    _create_workspace,
    consume_start_throttle,
    reserve_workspace,
)
from .base import DemoFilesystemMixin


class DemoWorkspaceServiceTests(DemoFilesystemMixin, TransactionTestCase):
    @override_settings(VANTA_DEMO_MAX_WORKSPACES=1)
    def test_capacity_reservation_is_atomic_on_postgresql(self):
        if connection.vendor != 'postgresql':
            self.skipTest('PostgreSQL row-lock behavior is exercised in CI.')

        barrier = Barrier(2)

        def reserve_once():
            close_old_connections()
            barrier.wait()
            try:
                reserve_workspace(uuid.uuid4())
            except DemoCapacityReached:
                return 'capacity'
            finally:
                connections['default'].close()
            return 'reserved'

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: reserve_once(), range(2)))

        self.assertCountEqual(results, ['reserved', 'capacity'])

    def test_two_browser_sessions_receive_isolated_workspace_files(self):
        first_client = Client()
        second_client = Client()
        self.assertEqual(self.start_demo(first_client).status_code, 302)
        self.assertEqual(self.start_demo(second_client).status_code, 302)

        first = DemoWorkspace.objects.get(
            pk=first_client.session[WORKSPACE_SESSION_KEY]
        )
        second = DemoWorkspace.objects.get(
            pk=second_client.session[WORKSPACE_SESSION_KEY]
        )
        self.assertNotEqual(first.pk, second.pk)

        first_alias = register_workspace_database(first.pk)
        second_alias = register_workspace_database(second.pk)
        try:
            with workspace_database(first_alias):
                post = BlogPost.objects.create(is_published=False, canonical_site_slug='vanta_admin')
                BlogPostTranslation.objects.create(
                    post=post,
                    language_code='en',
                    title='Only in the first browser',
                    slug='only-in-first-browser',
                    excerpt='Fictional test content.',
                )
            with workspace_database(second_alias):
                self.assertFalse(
                    BlogPostTranslation.objects.filter(slug='only-in-first-browser').exists()
                )
        finally:
            connections[first_alias].close()
            connections[second_alias].close()

    def test_reset_replaces_only_the_current_browser_workspace(self):
        first_client = Client()
        second_client = Client()
        self.start_demo(first_client)
        self.start_demo(second_client)
        old_first_id = first_client.session[WORKSPACE_SESSION_KEY]
        second_id = second_client.session[WORKSPACE_SESSION_KEY]

        first_client.get('/reset/')
        response = first_client.post(
            '/reset/', data='', content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(first_client.session[WORKSPACE_SESSION_KEY], old_first_id)
        self.assertEqual(second_client.session[WORKSPACE_SESSION_KEY], second_id)
        self.assertEqual(DemoWorkspace.objects.get(pk=old_first_id).status, 'retired')
        self.assertTrue(workspace_path(second_id).exists())

    def test_failed_reset_preserves_the_current_workspace(self):
        client = Client()
        self.start_demo(client)
        workspace_id = client.session[WORKSPACE_SESSION_KEY]
        client.get('/reset/')
        with patch(
            'apps.vanta_demo.services.workspaces._create_workspace',
            side_effect=DemoWorkspaceUnavailable,
        ):
            response = client.post(
                '/reset/', data='', content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(client.session[WORKSPACE_SESSION_KEY], workspace_id)
        self.assertTrue(workspace_path(workspace_id).exists())

    def test_failed_replacement_sign_in_preserves_the_current_workspace(self):
        client = Client()
        self.start_demo(client)
        workspace_id = client.session[WORKSPACE_SESSION_KEY]
        client.get('/reset/')
        with patch(
            'apps.vanta_demo.services.workspaces.sign_in_demo_admin',
            side_effect=RuntimeError('synthetic sign-in failure'),
        ):
            response = client.post(
                '/reset/', data='', content_type='application/x-www-form-urlencoded'
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(client.session[WORKSPACE_SESSION_KEY], workspace_id)
        current = DemoWorkspace.objects.get(pk=workspace_id)
        self.assertEqual(current.status, DemoWorkspace.Status.ACTIVE)
        self.assertTrue(workspace_path(workspace_id).exists())
        self.assertEqual(
            DemoWorkspace.objects.filter(status=DemoWorkspace.Status.FAILED).count(),
            1,
        )

    def test_overlapping_reset_uses_the_workspace_that_won_the_swap(self):
        client = Client()
        self.start_demo(client)
        current_id = client.session[WORKSPACE_SESSION_KEY]
        browser_id = uuid.UUID(client.session[BROWSER_SESSION_KEY])
        winner = _create_workspace(browser_id, replacement=True)
        client.get('/reset/')
        original_create_workspace = _create_workspace

        def finish_other_reset_then_create(browser_id, *, replacement=False):
            with transaction.atomic(using='default'):
                DemoWorkspace.objects.filter(pk=current_id).update(
                    status=DemoWorkspace.Status.RETIRED,
                    retired_at=timezone.now(),
                )
                DemoWorkspace.objects.filter(pk=winner.pk).update(browser_id=browser_id)
            return original_create_workspace(browser_id, replacement=replacement)

        with patch(
            'apps.vanta_demo.services.workspaces._create_workspace',
            side_effect=finish_other_reset_then_create,
        ):
            response = client.post(
                '/reset/', data='', content_type='application/x-www-form-urlencoded'
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.session[WORKSPACE_SESSION_KEY], str(winner.pk))
        self.assertEqual(
            DemoWorkspace.objects.filter(
                browser_id=browser_id,
                status=DemoWorkspace.Status.ACTIVE,
            ).count(),
            1,
        )
        discarded = DemoWorkspace.objects.exclude(pk__in=[current_id, winner.pk]).get()
        self.assertEqual(discarded.status, DemoWorkspace.Status.RETIRED)
        self.assertFalse(workspace_path(discarded.pk).exists())

    def test_expired_throttle_window_starts_a_new_window(self):
        request = RequestFactory().get('/', REMOTE_ADDR='203.0.113.41')
        started_at = timezone.now()
        with override_settings(
            VANTA_DEMO_START_LIMIT=1,
            VANTA_DEMO_START_WINDOW_SECONDS=60,
        ):
            consume_start_throttle(request, now=started_at)
            with self.assertRaises(DemoRateLimited):
                consume_start_throttle(request, now=started_at + timedelta(seconds=1))
            consume_start_throttle(request, now=started_at + timedelta(seconds=61))

        bucket = DemoThrottleBucket.objects.get()
        self.assertEqual(bucket.count, 1)
        self.assertEqual(bucket.window_started_at, started_at + timedelta(seconds=61))

    def test_throttle_stores_only_a_hash_and_returns_retry_after(self):
        client = Client(REMOTE_ADDR='203.0.113.40')
        with override_settings(VANTA_DEMO_START_LIMIT=1):
            self.start_demo(client)
            client.get('/reset/')
            response = client.post(
                '/reset/', data='', content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        bucket = DemoThrottleBucket.objects.get()
        self.assertEqual(len(bucket.key_hash), 64)
        self.assertNotIn('203.0.113.40', bucket.key_hash)


class DemoCleanupTests(DemoFilesystemMixin, TransactionTestCase):
    def test_cleanup_is_idempotent_and_dry_run_preserves_files(self):
        now = timezone.now()
        workspace = DemoWorkspace.objects.create(
            browser_id=uuid.uuid4(),
            status=DemoWorkspace.Status.EXPIRED,
            seed_version=settings.VANTA_DEMO_SEED_VERSION,
            last_activity_at=now - timedelta(hours=3),
            expires_at=now - timedelta(hours=1),
        )
        path = workspace_path(workspace.id)
        path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())

        call_command('cleanup_vanta_demo_workspaces', dry_run=True, limit=10, verbosity=0)
        self.assertTrue(path.exists())
        call_command('cleanup_vanta_demo_workspaces', limit=10, verbosity=0)
        call_command('cleanup_vanta_demo_workspaces', limit=10, verbosity=0)

        workspace.refresh_from_db()
        self.assertEqual(workspace.status, DemoWorkspace.Status.RETIRED)
        self.assertFalse(path.exists())

    def test_cleanup_handles_stale_rows_throttles_and_orphan_files(self):
        now = timezone.now()
        stale_creating = DemoWorkspace.objects.create(
            browser_id=uuid.uuid4(),
            seed_version=settings.VANTA_DEMO_SEED_VERSION,
            last_activity_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=1),
        )
        DemoWorkspace.objects.filter(pk=stale_creating.pk).update(
            created_at=now
            - timedelta(seconds=settings.VANTA_DEMO_CREATING_TIMEOUT_SECONDS + 1)
        )
        stale_path = workspace_path(stale_creating.pk)
        stale_path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())
        wrong_seed = DemoWorkspace.objects.create(
            browser_id=uuid.uuid4(),
            status=DemoWorkspace.Status.ACTIVE,
            seed_version='old-seed',
            last_activity_at=now,
            expires_at=now + timedelta(hours=1),
        )
        wrong_seed_path = workspace_path(wrong_seed.pk)
        wrong_seed_path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())
        DemoThrottleBucket.objects.create(
            key_hash='a' * 64,
            action=DemoThrottleBucket.Action.WORKSPACE_START,
            window_started_at=now - timedelta(minutes=2),
            count=1,
            expires_at=now - timedelta(minutes=1),
        )
        orphan_path = workspace_path(uuid.uuid4())
        orphan_path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())
        old_timestamp = now.timestamp() - settings.VANTA_DEMO_ORPHAN_MIN_AGE_SECONDS - 1
        os.utime(orphan_path, (old_timestamp, old_timestamp))

        call_command('cleanup_vanta_demo_workspaces', limit=10, verbosity=0)

        stale_creating.refresh_from_db()
        wrong_seed.refresh_from_db()
        self.assertEqual(stale_creating.status, DemoWorkspace.Status.RETIRED)
        self.assertEqual(wrong_seed.status, DemoWorkspace.Status.RETIRED)
        self.assertFalse(stale_path.exists())
        self.assertFalse(wrong_seed_path.exists())
        self.assertFalse(orphan_path.exists())
        self.assertFalse(DemoThrottleBucket.objects.exists())

    def test_cleanup_limit_bounds_each_cleanup_category(self):
        now = timezone.now()
        for index in range(2):
            workspace = DemoWorkspace.objects.create(
                browser_id=uuid.uuid4(),
                status=DemoWorkspace.Status.EXPIRED,
                seed_version=settings.VANTA_DEMO_SEED_VERSION,
                last_activity_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
            )
            workspace_path(workspace.pk).write_bytes(
                Path(settings.VANTA_DEMO_SEED_PATH).read_bytes()
            )
            DemoThrottleBucket.objects.create(
                key_hash=f'{index:064d}',
                action=DemoThrottleBucket.Action.WORKSPACE_START,
                window_started_at=now - timedelta(minutes=2),
                count=1,
                expires_at=now - timedelta(minutes=1),
            )

        orphan_paths = [workspace_path(uuid.uuid4()) for _ in range(2)]
        old_timestamp = now.timestamp() - settings.VANTA_DEMO_ORPHAN_MIN_AGE_SECONDS - 1
        for path in orphan_paths:
            path.write_bytes(Path(settings.VANTA_DEMO_SEED_PATH).read_bytes())
            os.utime(path, (old_timestamp, old_timestamp))

        call_command('cleanup_vanta_demo_workspaces', limit=1, verbosity=0)

        self.assertEqual(
            DemoWorkspace.objects.filter(status=DemoWorkspace.Status.RETIRED).count(),
            1,
        )
        self.assertEqual(DemoThrottleBucket.objects.count(), 1)
        self.assertEqual(sum(path.exists() for path in orphan_paths), 1)
