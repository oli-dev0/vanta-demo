from datetime import timedelta
from urllib.parse import urlencode
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone

from apps.demo_contact.models import ContactMessage
from apps.demo_content.models import (
    AuthorProfile, BlogCategory, BlogImage, BlogImageComparison, BlogPost,
    BlogPostRelated, BlogTag,
)
from apps.demo_newsletter.models import (
    Campaign, CampaignDelivery, NewsletterImage, NewsletterSite, Subscription,
)
from apps.demo_projects.models import Project
from apps.demo_status.models import Incident, KumaMonitor, StatusPage

from apps.vanta_demo.admin import demo_admin_site
from apps.vanta_demo.context import get_workspace_alias
from apps.vanta_demo.database import workspace_path
from apps.vanta_demo.models import DemoWorkspace
from apps.vanta_demo.services.workspaces import RESET_PREFERENCES_SESSION_KEY, WORKSPACE_SESSION_KEY
from apps.vanta_demo.views import server_error
from .base import DemoFilesystemMixin


class DemoPublicViewTests(DemoFilesystemMixin, TransactionTestCase):
    def test_overview_has_public_metadata_and_copy(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vanta Admin Demo | Try the Django Admin Theme')
        self.assertContains(response, 'https://demo.vanta-admin.org/')
        self.assertContains(response, 'Running Vanta Admin 0.23.0 · Django 6.1')
        self.assertContains(response, 'Try the demo')
        self.assertContains(response, 'newsletters, service status, contact messages')
        self.assertEqual(response.headers['Cache-Control'], 'private, no-cache')
        self.assertEqual(response.headers['X-Robots-Tag'], 'index, follow')

    def test_start_requires_the_session_cookie(self):
        client = Client()
        client.get('/')
        client.cookies.clear()
        response = client.post(
            '/start/', data='', content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Essential cookies are required.', status_code=400)

    def test_start_requires_csrf_and_accepts_the_overview_token(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/')
        rejected = client.post(
            '/start/', data='', content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(rejected.headers['X-Robots-Tag'], 'noindex, noarchive')

        token = client.cookies['csrftoken'].value
        client.get('/')
        accepted = client.post(
            '/start/',
            urlencode({'csrfmiddlewaretoken': token}),
            content_type='application/x-www-form-urlencoded',
        )
        self.assertRedirects(accepted, '/admin/', fetch_redirect_response=False)

    def test_multipart_requests_are_rejected(self):
        self.client.get('/')
        response = self.client.post('/start/', {'unexpected': 'upload-like request'})
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.headers['X-Robots-Tag'], 'noindex, noarchive')

    @override_settings(VANTA_DEMO_MAX_WORKSPACES=0)
    def test_capacity_response_is_retryable_and_noindex(self):
        response = self.start_demo()
        self.assertEqual(response.status_code, 503)
        self.assertIn('Retry-After', response)
        self.assertEqual(response.headers['X-Robots-Tag'], 'noindex, noarchive')

    def test_robots_and_sitemap_expose_only_public_overview(self):
        robots = self.client.get('/robots.txt')
        sitemap = self.client.get('/sitemap.xml')
        self.assertContains(robots, 'Disallow: /admin/')
        self.assertContains(robots, 'Disallow: /reset/')
        self.assertContains(sitemap, '<loc>https://demo.vanta-admin.org/</loc>')
        self.assertNotContains(sitemap, '/admin/')

    def test_liveness_does_not_create_a_session_or_workspace(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('vanta_demo_sessionid', response.cookies)
        self.assertFalse(DemoWorkspace.objects.exists())

    def test_readiness_checks_database_seed_and_volume(self):
        self.assertEqual(self.client.get('/readyz/').status_code, 200)
        with override_settings(VANTA_DEMO_SEED_PATH='/tmp/missing-vanta-demo-seed.sqlite3'):
            response = self.client.get('/readyz/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['X-Robots-Tag'], 'noindex, noarchive')

    def test_server_error_returns_a_safe_request_reference(self):
        request = self.client.get('/').wsgi_request
        with patch('apps.vanta_demo.views.logger.exception'):
            response = server_error(request)
        request_reference = response.headers['X-Request-ID']
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(request_reference), 16)
        self.assertContains(response, request_reference, status_code=500)


class DemoAdminTests(DemoFilesystemMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.start_demo()

    def test_admin_registers_only_the_allowlisted_models(self):
        self.assertEqual(
            set(demo_admin_site._registry),
            {
                get_user_model(), Group, AuthorProfile, BlogPost, BlogCategory, BlogTag,
                BlogImage, BlogImageComparison, BlogPostRelated, Project, NewsletterSite,
                Subscription, NewsletterImage, Campaign, CampaignDelivery, StatusPage,
                KumaMonitor, Incident, ContactMessage,
            },
        )

    def test_admin_shows_notice_dashboard_and_long_user_list(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo mode')
        self.assertContains(response, 'Demo Admin')
        self.assertContains(response, 'Fictional workflow note')
        self.assertNotContains(response, 'Demo data')
        self.assertContains(response, 'My recent activity')
        self.assertContains(response, 'Quick actions')
        self.assertContains(response, 'Attention required')
        self.assertContains(response, 'Configure project shortcuts for this dashboard.')
        self.assertContains(response, 'Configure project-specific checks to show items that need attention.')
        dashboard = response.content.decode()
        self.assertLess(dashboard.index('My recent activity'), dashboard.index('Quick actions'))
        self.assertLess(dashboard.index('Attention required'), dashboard.index('System'))
        self.assertLess(dashboard.index('System'), dashboard.index('Environment'))
        self.assertIsNone(get_workspace_alias())
        users = self.client.get('/admin/auth/user/')
        self.assertEqual(users.status_code, 200)
        self.assertContains(users, 'demo-admin')
        self.assertContains(users, 'id="action-toggle"')
        self.assertContains(users, 'name="action"')
        self.assertContains(users, 'Showing 1 to 10 of 24 users')
        self.assertContains(users, 'admin-pagination-pages')
        self.assertContains(users, 'data-admin-pagination-jump')
        self.assertContains(users, 'admin/js/pagination-jump.js')

    def test_project_changelist_uses_names_and_labels_sorting_id(self):
        response = self.client.get('/admin/demo_projects/project/')

        self.assertContains(response, 'Northstar')
        self.assertContains(response, 'column-project_name')
        self.assertContains(response, '>ID<')
        self.assertContains(response, 'Showing 1 to 10 of 24 projects')
        self.assertContains(response, 'admin-pagination-pages')
        self.assertContains(response, 'data-admin-pagination-jump')
        self.assertNotContains(response, 'Fictional project 01')

    def test_blog_changelist_does_not_render_date_hierarchy(self):
        response = self.client.get('/admin/demo_content/blogpost/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="toplinks"')

    def test_change_form_keeps_only_the_bottom_submit_row(self):
        response = self.client.get('/admin/demo_projects/project/1/change/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(b'class="submit-row"'), 1)
        self.assertContains(response, 'data-inline-type="stacked"')
        self.assertNotContains(response, 'data-inline-type="tabular"')

    def test_blog_translation_inline_uses_readable_stacked_layout(self):
        response = self.client.get('/admin/demo_content/blogpost/1/change/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-inline-type="stacked"')
        self.assertContains(response, 'demo-blog-translations')

    def test_expanded_admin_sections_and_paginated_data_are_available(self):
        dashboard = self.client.get('/admin/')
        for section in ('Blog', 'Projects', 'Newsletter', 'Status', 'Contact'):
            self.assertContains(dashboard, section)
        self.assertContains(dashboard, '<dt>Django version</dt><dd>6.1</dd>', html=True)

        subscriptions = self.client.get('/admin/demo_newsletter/subscription/')
        self.assertContains(subscriptions, 'Showing 1 to 10 of 80 subscriptions')
        self.assertContains(subscriptions, 'subscriber-080@example.invalid')
        contacts = self.client.get('/admin/demo_contact/contactmessage/')
        self.assertContains(contacts, 'Showing 1 to 10 of 60 contact messages')

    def test_operational_integration_actions_are_not_exposed(self):
        campaigns = self.client.get('/admin/demo_newsletter/campaign/')
        monitors = self.client.get('/admin/demo_status/kumamonitor/')
        for forbidden in ('Send campaign', 'Retry delivery', 'Preview email'):
            self.assertNotContains(campaigns, forbidden)
        self.assertNotContains(monitors, 'Fetch from Kuma')

    def test_reset_clears_vanta_preferences_once(self):
        self.client.get('/reset/')
        reset_response = self.client.post(
            '/reset/', data='', content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(reset_response.status_code, 302)
        self.assertTrue(self.client.session[RESET_PREFERENCES_SESSION_KEY])

        first_admin = self.client.get('/admin/')
        for key in (
            'theme',
            'django.admin.theme.timeFormat',
            'django.admin.theme.fontSize',
            'django.admin.theme.sidebar.isCollapsed',
            'django.admin.theme.sidebar.width',
            'django.admin.theme.sidebar.openSections',
            'django.admin.theme.sidebar.sectionOrder',
        ):
            self.assertContains(first_admin, key)
        self.assertContains(first_admin, 'localStorage.removeItem(key)')
        self.assertNotIn(RESET_PREFERENCES_SESSION_KEY, self.client.session)

        second_admin = self.client.get('/admin/')
        self.assertNotContains(second_admin, 'localStorage.removeItem(key)')

    def test_direct_login_and_password_routes_do_not_show_credentials(self):
        self.assertRedirects(self.client.get('/admin/login/'), '/', fetch_redirect_response=False)
        self.assertRedirects(
            self.client.get('/admin/password_change/'),
            '/reset/',
            fetch_redirect_response=False,
        )

    def test_demo_admin_cannot_be_deleted_or_demoted(self):
        response = self.client.get('/admin/auth/user/1/delete/')
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            '/admin/auth/user/1/change/',
            urlencode(
                {
                    'username': 'demo-admin',
                    'first_name': 'Demo',
                    'last_name': 'Admin',
                    'email': 'demo-admin@example.invalid',
                    'is_staff': '',
                    '_save': 'Save',
                }
            ),
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'synthetic Demo Admin account is protected')

    def test_expired_workspace_redirects_to_safe_state(self):
        workspace_id = self.client.session[WORKSPACE_SESSION_KEY]
        DemoWorkspace.objects.filter(pk=workspace_id).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/expired/', fetch_redirect_response=False)

    def test_seed_version_mismatch_expires_the_workspace(self):
        workspace_id = self.client.session[WORKSPACE_SESSION_KEY]
        DemoWorkspace.objects.filter(pk=workspace_id).update(seed_version='old-seed')
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/expired/', fetch_redirect_response=False)
        self.assertEqual(
            DemoWorkspace.objects.get(pk=workspace_id).status,
            DemoWorkspace.Status.EXPIRED,
        )

    def test_missing_workspace_file_fails_closed(self):
        workspace_id = self.client.session[WORKSPACE_SESSION_KEY]
        workspace_path(workspace_id).unlink()

        response = self.client.get('/admin/')

        self.assertRedirects(response, '/expired/', fetch_redirect_response=False)
        self.assertNotIn(WORKSPACE_SESSION_KEY, self.client.session)
        workspace = DemoWorkspace.objects.get(pk=workspace_id)
        self.assertEqual(workspace.status, DemoWorkspace.Status.FAILED)
        self.assertEqual(workspace.failure_code, 'workspace_invalid')
