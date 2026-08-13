import os
from pathlib import Path

os.environ.setdefault('DJANGO_DEBUG', 'False')
os.environ.setdefault('DJANGO_SECRET_KEY', 'demo-seed-build-only')
os.environ.setdefault('DATABASE_URL', f"sqlite:///{Path('/tmp/vanta-demo-control.sqlite3')}")
os.environ.setdefault('VANTA_DEMO_HASH_SECRET', 'demo-seed-build-only')
os.environ.setdefault('VANTA_DEMO_SKIP_RUNTIME_CHECKS', 'True')
os.environ.setdefault('VANTA_DEMO_SEED_BUILD', 'True')

from .base import *  # noqa: E402,F403

DEBUG = False
VANTA_DEMO_SEED_BUILD = True

