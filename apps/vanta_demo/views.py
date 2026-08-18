import logging
import os
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.db import DatabaseError, connection
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .services import (
    DemoCapacityReached,
    DemoCookiesRequired,
    DemoRateLimited,
    DemoWorkspaceUnavailable,
    reset_workspace,
    start_or_resume_workspace,
)
from .services.workspaces import (
    RESET_PREFERENCES_SESSION_KEY,
    ensure_browser_session,
    issue_start_marker,
    validate_workspace_file,
)
from .models import DemoCapacityLock


logger = logging.getLogger(__name__)


STATE_CONTENT = {
    'cookie_required': {
        'title': _('Essential cookies are required.'),
        'body': _('The demo uses an essential session cookie to keep your workspace private.'),
        'action': _('Back to demo overview'),
        'action_url_name': 'vanta_demo:overview',
    },
    'capacity': {
        'title': _('The demo is busy right now.'),
        'body': _('Please wait a moment and try again.'),
        'action': _('Try again'),
        'action_url_name': 'vanta_demo:start',
        'post_action': True,
    },
    'rate_limit': {
        'title': _('Please wait before starting another demo.'),
        'body': _('This temporary limit protects the private demo workspaces.'),
        'action': _('Try again'),
        'action_url_name': 'vanta_demo:start',
        'post_action': True,
    },
    'expired': {
        'title': _('Your demo workspace has expired.'),
        'body': _('Demo workspaces are temporary, so the previous changes are no longer available.'),
        'action': _('Start a new demo'),
        'action_url_name': 'vanta_demo:start',
        'post_action': True,
    },
    'unavailable': {
        'title': _('We could not open the demo right now.'),
        'body': _('Please try again.'),
        'action': _('Try again'),
        'action_url_name': 'vanta_demo:start',
        'post_action': True,
    },
    'bad_request': {
        'title': _('That request could not be completed.'),
        'body': _('Return to the demo overview and try again.'),
        'action': _('Back to demo overview'),
        'action_url_name': 'vanta_demo:overview',
    },
    'permission_denied': {
        'title': _('This demo action is not available.'),
        'body': _('Return to your workspace or start a fresh demo.'),
        'action': _('Back to demo overview'),
        'action_url_name': 'vanta_demo:overview',
    },
    'not_found': {
        'title': _('This demo page was not found.'),
        'body': _('The link may be stale because demo workspaces are temporary.'),
        'action': _('Back to demo overview'),
        'action_url_name': 'vanta_demo:overview',
    },
    'server_error': {
        'title': _('We could not open the demo right now.'),
        'body': _('Please try again.'),
        'action': _('Back to demo overview'),
        'action_url_name': 'vanta_demo:overview',
    },
}


def _private_response(response, *, noindex=True):
    response.headers['Cache-Control'] = 'no-store, private'
    if noindex:
        response.headers['X-Robots-Tag'] = 'noindex, noarchive'
    return response


def state_response(request, state, *, status=200, retry_after=None, request_reference=None):
    content = STATE_CONTENT[state]
    if content.get('post_action'):
        ensure_browser_session(request)
        issue_start_marker(request)
    response = render(
        request,
        'vanta_demo/state.html',
        {
            'state': state,
            'request_reference': request_reference,
            **content,
        },
        status=status,
    )
    if retry_after:
        response.headers['Retry-After'] = str(max(1, int(retry_after)))
    return _private_response(response)


@require_GET
def overview(request):
    ensure_browser_session(request)
    issue_start_marker(request)
    response = render(request, 'vanta_demo/overview.html')
    response.headers['Cache-Control'] = 'private, no-cache'
    response.headers['X-Robots-Tag'] = 'index, follow'
    return response


@require_POST
@never_cache
def start(request):
    try:
        start_or_resume_workspace(request)
    except DemoCookiesRequired:
        return state_response(request, 'cookie_required', status=400)
    except DemoRateLimited as error:
        return state_response(
            request,
            'rate_limit',
            status=429,
            retry_after=error.retry_after,
        )
    except DemoCapacityReached:
        return state_response(
            request,
            'capacity',
            status=503,
            retry_after=settings.VANTA_DEMO_RETRY_AFTER_SECONDS,
        )
    except DemoWorkspaceUnavailable:
        return state_response(
            request,
            'unavailable',
            status=503,
            retry_after=settings.VANTA_DEMO_RETRY_AFTER_SECONDS,
        )
    return _private_response(redirect('admin:index'))


@require_http_methods(['GET', 'POST'])
@never_cache
def reset(request):
    if request.method == 'GET':
        ensure_browser_session(request)
        issue_start_marker(request)
        response = render(
            request,
            'vanta_demo/reset.html',
            {'cancel_url': reverse('admin:index') if hasattr(request, 'demo_workspace') else '/'},
        )
        return _private_response(response)

    try:
        reset_workspace(request)
    except DemoCookiesRequired:
        return state_response(request, 'cookie_required', status=400)
    except DemoRateLimited as error:
        return state_response(
            request,
            'rate_limit',
            status=429,
            retry_after=error.retry_after,
        )
    except DemoCapacityReached:
        return state_response(
            request,
            'capacity',
            status=503,
            retry_after=settings.VANTA_DEMO_RETRY_AFTER_SECONDS,
        )
    except DemoWorkspaceUnavailable:
        return state_response(
            request,
            'unavailable',
            status=503,
            retry_after=settings.VANTA_DEMO_RETRY_AFTER_SECONDS,
        )
    request.session[RESET_PREFERENCES_SESSION_KEY] = True
    messages.success(request, _('A fresh private demo workspace is ready.'))
    return _private_response(redirect('admin:index'))


@require_GET
def expired(request):
    return state_response(request, 'expired')


@require_GET
def robots_txt(request):
    del request
    body = '\n'.join(
        [
            'User-agent: *',
            'Disallow: /admin/',
            'Disallow: /start/',
            'Disallow: /reset/',
            'Disallow: /expired/',
            'Sitemap: https://demo.vanta-admin.org/sitemap.xml',
            '',
        ]
    )
    return HttpResponse(body, content_type='text/plain; charset=utf-8')


@require_GET
def sitemap_xml(request):
    del request
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>https://demo.vanta-admin.org/</loc></url>'
        '</urlset>'
    )
    return HttpResponse(body, content_type='application/xml; charset=utf-8')


@require_GET
def healthz(request):
    del request
    response = HttpResponse('ok', content_type='text/plain; charset=utf-8')
    return _private_response(response)


@require_GET
def readyz(request):
    del request
    ready = True
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        if not DemoCapacityLock.objects.using('default').filter(pk=1).exists():
            ready = False
    except DatabaseError:
        ready = False

    root = Path(settings.VANTA_DEMO_WORKSPACE_ROOT)
    seed = Path(settings.VANTA_DEMO_SEED_PATH)
    if not root.is_dir() or not os.access(root, os.W_OK | os.X_OK):
        ready = False
    if not seed.is_file() or not validate_workspace_file(seed):
        ready = False
    response = HttpResponse(
        'ready' if ready else 'not ready',
        status=200 if ready else 503,
        content_type='text/plain; charset=utf-8',
    )
    return _private_response(response)


@require_GET
def favicon(request):
    del request
    return redirect(static('vanta_site/img/logo.svg'), permanent=False)


def bad_request(request, exception=None):
    del exception
    return state_response(request, 'bad_request', status=400)


def permission_denied(request, exception=None):
    del exception
    return state_response(request, 'permission_denied', status=403)


def csrf_failure(request, reason=''):
    del reason
    return state_response(request, 'permission_denied', status=403)


def page_not_found(request, exception=None):
    del exception
    return state_response(request, 'not_found', status=404)


def server_error(request):
    request_reference = secrets.token_hex(8)
    logger.exception(
        'Vanta demo request failed request_reference=%s',
        request_reference,
    )
    response = state_response(
        request,
        'server_error',
        status=500,
        request_reference=request_reference,
    )
    response.headers['X-Request-ID'] = request_reference
    return response
