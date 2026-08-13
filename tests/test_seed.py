import sqlite3
import tempfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import is_password_usable
from django.core.management import call_command
from django.test import TransactionTestCase
from django.utils import timezone

from apps.vanta_demo.database import workspace_path
from apps.vanta_demo.services.workspaces import validate_workspace_file
from .base import DemoFilesystemMixin


class DemoSeedTests(DemoFilesystemMixin, TransactionTestCase):

    def test_docker_build_uses_current_seed_version(self):
        dockerfile = (settings.BASE_DIR / 'Dockerfile').read_text()
        expected_path = (
            'VANTA_DEMO_SEED_PATH=/app/demo-seed/'
            f'vanta-demo-{settings.VANTA_DEMO_SEED_VERSION}.sqlite3'
        )

        self.assertEqual(dockerfile.count(expected_path), 2)

    def test_seed_contains_deterministic_fictional_dataset_and_unusable_passwords(self):
        with tempfile.TemporaryDirectory(prefix='vanta-seed-test-') as directory:
            first = Path(directory) / 'first.sqlite3'
            second = Path(directory) / 'second.sqlite3'
            call_command('build_vanta_demo_seed', destination=first, force=True, verbosity=0)
            call_command('build_vanta_demo_seed', destination=second, force=True, verbosity=0)

            self.assertTrue(validate_workspace_file(first))
            first_snapshot = self._snapshot(first)
            self.assertEqual(first_snapshot, self._snapshot(second))
            self.assertEqual(
                {key: value for key, value in first_snapshot.items() if key != 'admin'},
                {
                    'users': 24, 'posts': 60, 'authors': 12, 'images': 30,
                    'projects': 24, 'subscriptions': 80, 'campaigns': 24,
                    'deliveries': 80, 'monitors': 12, 'incidents': 24,
                    'updates': 48, 'contacts': 60, 'history': 30,
                },
            )
            with sqlite3.connect(first) as connection:
                passwords = connection.execute('SELECT password FROM auth_user').fetchall()
                subscription_emails = connection.execute(
                    'SELECT email FROM demo_newsletter_subscription'
                ).fetchall()
                activity_dates = {
                    row[0][:10]
                    for row in connection.execute(
                        'SELECT action_time FROM django_admin_log'
                    ).fetchall()
                }
            self.assertTrue(passwords)
            self.assertTrue(all(not is_password_usable(password) for (password,) in passwords))
            self.assertTrue(
                all(email.endswith('@example.invalid') for (email,) in subscription_emails)
            )
            self.assertEqual(activity_dates, {'2026-07-01', '2026-06-30'})

    def test_materialized_workspace_refreshes_activity_to_today_and_yesterday(self):
        response = self.start_demo()
        self.assertEqual(response.status_code, 302, response.content)
        workspace_id = self.client.session['vanta_demo_workspace_id']

        with sqlite3.connect(workspace_path(workspace_id)) as connection:
            activity_dates = {
                row[0][:10]
                for row in connection.execute(
                    'SELECT action_time FROM django_admin_log'
                ).fetchall()
            }

        today = timezone.localdate()
        self.assertEqual(activity_dates, {str(today), str(today - timedelta(days=1))})

    def _snapshot(self, path):
        with sqlite3.connect(path) as connection:
            admin = connection.execute(
                "SELECT username, password, is_staff, is_superuser FROM auth_user WHERE username='demo-admin'"
            ).fetchone()
            return {
                'admin': admin,
                'users': connection.execute('SELECT COUNT(*) FROM auth_user').fetchone()[0],
                'posts': connection.execute('SELECT COUNT(*) FROM demo_content_blogpost').fetchone()[0],
                'authors': connection.execute('SELECT COUNT(*) FROM demo_content_authorprofile').fetchone()[0],
                'images': connection.execute('SELECT COUNT(*) FROM demo_content_blogimage').fetchone()[0],
                'projects': connection.execute('SELECT COUNT(*) FROM demo_projects_project').fetchone()[0],
                'subscriptions': connection.execute('SELECT COUNT(*) FROM demo_newsletter_subscription').fetchone()[0],
                'campaigns': connection.execute('SELECT COUNT(*) FROM demo_newsletter_campaign').fetchone()[0],
                'deliveries': connection.execute('SELECT COUNT(*) FROM demo_newsletter_campaigndelivery').fetchone()[0],
                'monitors': connection.execute('SELECT COUNT(*) FROM demo_status_kumamonitor').fetchone()[0],
                'incidents': connection.execute('SELECT COUNT(*) FROM demo_status_incident').fetchone()[0],
                'updates': connection.execute('SELECT COUNT(*) FROM demo_status_incidentupdate').fetchone()[0],
                'contacts': connection.execute('SELECT COUNT(*) FROM demo_contact_contactmessage').fetchone()[0],
                'history': connection.execute('SELECT COUNT(*) FROM django_admin_log').fetchone()[0],
            }
