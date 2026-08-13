import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .env import get_bool_env, get_int_env, get_list_env, get_required_env, get_required_list_env


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEBUG = get_bool_env('DJANGO_DEBUG', False)
IS_SEED_BUILD = get_bool_env('VANTA_DEMO_SEED_BUILD', False)
SECRET_KEY = get_required_env('DJANGO_SECRET_KEY') if not DEBUG else os.environ.get('DJANGO_SECRET_KEY', 'local-demo-only')

if DEBUG or IS_SEED_BUILD:
    ALLOWED_HOSTS = get_list_env(
        'DJANGO_ALLOWED_HOSTS',
        ['demo.vanta.localhost', 'localhost', '127.0.0.1', 'testserver'],
    )
    CSRF_TRUSTED_ORIGINS = get_list_env(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        ['http://demo.vanta.localhost:8001'],
    )
else:
    ALLOWED_HOSTS = get_required_list_env('DJANGO_ALLOWED_HOSTS')
    CSRF_TRUSTED_ORIGINS = get_required_list_env('DJANGO_CSRF_TRUSTED_ORIGINS')

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ImproperlyConfigured('DATABASE_URL must be set.')

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=get_int_env('DATABASE_CONN_MAX_AGE', 60),
        conn_health_checks=True,
    ),
}
if (
    not DEBUG
    and not IS_SEED_BUILD
    and DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
):
    raise ImproperlyConfigured('The production Vanta demo control database must use PostgreSQL.')

INSTALLED_APPS = [
    'vanta_admin',
    'apps.vanta_demo.admin_apps.DemoAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.vanta_demo.apps.VantaDemoConfig',
    'apps.demo_content.apps.DemoContentConfig',
    'apps.demo_projects.apps.DemoProjectsConfig',
    'apps.demo_newsletter.apps.DemoNewsletterConfig',
    'apps.demo_status.apps.DemoStatusConfig',
    'apps.demo_contact.apps.DemoContactConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.vanta_demo.middleware.DemoWorkspaceMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.demo_urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'apps' / 'vanta_demo' / 'templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.vanta_demo.context_processors.demo_metadata',
            ],
        },
    },
]

DATABASE_ROUTERS = ['apps.vanta_demo.database.DemoWorkspaceRouter']
AUTHENTICATION_BACKENDS = ['apps.vanta_demo.backends.DemoWorkspaceBackend']
LOGIN_URL = '/'
CSRF_FAILURE_VIEW = 'apps.vanta_demo.views.csrf_failure'

LANGUAGE_CODE = 'en'
LANGUAGES = [('en', 'English')]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_NAME = 'vanta_demo_sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = get_bool_env('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = get_bool_env('CSRF_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_HTTPONLY = get_bool_env('CSRF_COOKIE_HTTPONLY', False)
SECURE_SSL_REDIRECT = get_bool_env('SECURE_SSL_REDIRECT', not DEBUG)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = get_int_env('SECURE_HSTS_SECONDS', 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool_env('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = get_bool_env('SECURE_HSTS_PRELOAD', False)
X_FRAME_OPTIONS = 'DENY'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

DATA_UPLOAD_MAX_MEMORY_SIZE = get_int_env('VANTA_DEMO_MAX_REQUEST_BYTES', 262_144)
DATA_UPLOAD_MAX_NUMBER_FIELDS = get_int_env('VANTA_DEMO_MAX_FORM_FIELDS', 500)
VANTA_DEMO_WORKSPACE_ROOT = Path(os.environ.get('VANTA_DEMO_WORKSPACE_ROOT', '/app/demo-workspaces')).resolve()
VANTA_DEMO_SEED_VERSION = '0.22.2-1'
VANTA_DEMO_SEED_PATH = BASE_DIR / 'demo-seed' / f'vanta-demo-{VANTA_DEMO_SEED_VERSION}.sqlite3'
if DEBUG or IS_SEED_BUILD:
    VANTA_DEMO_SEED_PATH = Path(
        os.environ.get('VANTA_DEMO_SEED_PATH', VANTA_DEMO_SEED_PATH)
    ).resolve()
VANTA_DEMO_WORKSPACE_TTL_SECONDS = get_int_env('VANTA_DEMO_WORKSPACE_TTL_SECONDS', 7200)
VANTA_DEMO_MAX_WORKSPACES = get_int_env('VANTA_DEMO_MAX_WORKSPACES', 100)
VANTA_DEMO_START_LIMIT = get_int_env('VANTA_DEMO_START_LIMIT', 5)
VANTA_DEMO_START_WINDOW_SECONDS = get_int_env('VANTA_DEMO_START_WINDOW_SECONDS', 600)
VANTA_DEMO_HASH_SECRET = os.environ.get('VANTA_DEMO_HASH_SECRET', '')
VANTA_DEMO_TRUSTED_IP_HEADER = os.environ.get('VANTA_DEMO_TRUSTED_IP_HEADER', 'HTTP_CF_CONNECTING_IP')
VANTA_DEMO_SQLITE_TIMEOUT_SECONDS = get_int_env('VANTA_DEMO_SQLITE_TIMEOUT_SECONDS', 5)
VANTA_DEMO_ACTIVITY_REFRESH_SECONDS = get_int_env('VANTA_DEMO_ACTIVITY_REFRESH_SECONDS', 60)
VANTA_DEMO_CREATING_TIMEOUT_SECONDS = get_int_env('VANTA_DEMO_CREATING_TIMEOUT_SECONDS', 300)
VANTA_DEMO_ORPHAN_MIN_AGE_SECONDS = get_int_env('VANTA_DEMO_ORPHAN_MIN_AGE_SECONDS', 900)
VANTA_DEMO_RETRY_AFTER_SECONDS = get_int_env('VANTA_DEMO_RETRY_AFTER_SECONDS', 60)
VANTA_DEMO_MODEL_RECORD_CAP = get_int_env('VANTA_DEMO_MODEL_RECORD_CAP', 100)
VANTA_DEMO_SKIP_RUNTIME_CHECKS = get_bool_env('VANTA_DEMO_SKIP_RUNTIME_CHECKS', False)
