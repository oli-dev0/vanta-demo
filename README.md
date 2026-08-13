# Vanta Admin Demo

This repository powers the interactive [Vanta Admin demo](https://demo.vanta-admin.org/).
It is a small, standalone Django application built around the released Vanta
Admin package.

The demo gives you a real admin area to explore rather than a set of screenshots.
You can browse lists, search and filter records, open forms, try bulk actions,
change settings, and see how the theme behaves with realistic content. The data
is fictional, and the changes you make are yours alone inside a temporary
workspace for your browser.

That makes the demo useful for two things: getting a feel for Vanta Admin as a
visitor, and seeing how a Django project can integrate the theme without
building a separate frontend application.

## Local development

The commands below build the same kind of seed data used by the demo, prepare a
local control database, and start the site at `http://demo.vanta.localhost:8001/`.

```bash
mkdir -p /tmp/vanta-demo-workspaces

DJANGO_SETTINGS_MODULE=config.settings.demo_seed \
VANTA_DEMO_SEED_PATH=/tmp/vanta-demo-seed.sqlite3 \
uv run python manage.py build_vanta_demo_seed --force

DJANGO_SETTINGS_MODULE=config.settings.demo \
DJANGO_DEBUG=True \
DJANGO_SECRET_KEY=local-demo-only \
DATABASE_URL=sqlite:////tmp/vanta-demo-control.sqlite3 \
DJANGO_ALLOWED_HOSTS=demo.vanta.localhost,localhost,127.0.0.1 \
DJANGO_CSRF_TRUSTED_ORIGINS=http://demo.vanta.localhost:8001 \
VANTA_DEMO_HASH_SECRET=local-demo-hash-only \
VANTA_DEMO_WORKSPACE_ROOT=/tmp/vanta-demo-workspaces \
VANTA_DEMO_SEED_PATH=/tmp/vanta-demo-seed.sqlite3 \
uv run python manage.py migrate --noinput

DJANGO_SETTINGS_MODULE=config.settings.demo \
DJANGO_DEBUG=True \
DJANGO_SECRET_KEY=local-demo-only \
DATABASE_URL=sqlite:////tmp/vanta-demo-control.sqlite3 \
DJANGO_ALLOWED_HOSTS=demo.vanta.localhost,localhost,127.0.0.1 \
DJANGO_CSRF_TRUSTED_ORIGINS=http://demo.vanta.localhost:8001 \
VANTA_DEMO_HASH_SECRET=local-demo-hash-only \
VANTA_DEMO_WORKSPACE_ROOT=/tmp/vanta-demo-workspaces \
VANTA_DEMO_SEED_PATH=/tmp/vanta-demo-seed.sqlite3 \
uv run python manage.py runserver 8001
```

Open `http://demo.vanta.localhost:8001/`.

## Verification

Run the focused checks with the demo's local settings:

```bash
uv run ruff check .
DJANGO_SETTINGS_MODULE=config.settings.demo \
DJANGO_DEBUG=True \
DJANGO_SECRET_KEY=test-only \
DATABASE_URL=sqlite:////tmp/vanta-demo-test.sqlite3 \
VANTA_DEMO_HASH_SECRET=test-only \
VANTA_DEMO_WORKSPACE_ROOT=/tmp/vanta-demo-test-workspaces \
VANTA_DEMO_SEED_PATH=/tmp/vanta-demo-seed.sqlite3 \
uv run python manage.py test tests
```

## How it works

Each browser gets a short-lived workspace copied from a deterministic seed. The
workspace contains fictional users, blog content, projects, newsletter data,
status records, contact messages, and admin history. You can edit the records
normally, but the workspace is disposable and is not shared with anyone else.

The demo keeps workspace control data separate from the editable SQLite file.
That boundary is what makes it safe to let visitors try real create, change, and
delete flows without connecting the demo to an application's own data.

For the implementation details, start with the [documentation index](docs/README.md).
