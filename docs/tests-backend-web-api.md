# Backend and web/API tests

## Targeted suite

Run the isolated suite with the demo settings and disposable local paths:

```bash
DJANGO_SETTINGS_MODULE=config.settings.demo \
DJANGO_DEBUG=True \
DJANGO_SECRET_KEY=demo-test-only \
DATABASE_URL=sqlite:////tmp/vanta-demo-control.sqlite3 \
VANTA_DEMO_HASH_SECRET=demo-test-only \
VANTA_DEMO_WORKSPACE_ROOT=/tmp/vanta-demo-workspaces \
VANTA_DEMO_SEED_PATH=/tmp/vanta-demo-seed.sqlite3 \
VANTA_DEMO_SKIP_RUNTIME_CHECKS=True \
uv run --no-sync python manage.py test tests
```

The exact local validation on 2026-08-07 built the seed and ran 50 tests: 49 passed with one expected PostgreSQL-only capacity-lock test skipped under SQLite. Ruff, migration-drift detection, and `git diff --check` also passed.

## Coverage map

- `test_models_database.py`: singleton capacity lock, one live workspace per browser, active-state/version/expiry rules, control/workspace routing, path safety, and credential-free backend behavior.
- `test_services.py`: PostgreSQL atomic capacity reservation, two-browser file isolation, reset replacement and failure preservation, concurrent reset winner behavior, throttle windows/hash storage, idempotent/dry-run cleanup, stale rows, orphan files, and bounded cleanup.
- `test_views_admin.py`: public metadata and copy, cookie/CSRF/content-type enforcement, capacity and retry headers, robots/sitemap, liveness/readiness, safe server-error reference, expanded admin allowlist/dashboard, richer paginated changelists, absent operational integration actions, preference reset, direct login/password routes, protected synthetic user, expiry, seed mismatch, and missing-file fail-closed behavior.
- `test_forms_admin.py`: 5,000-character server validation, inline `validate_max` configuration, and the no-file-field workspace boundary.
- `test_seed.py`: Docker/runtime seed-version alignment, deterministic seed snapshots, expanded model counts, reserved `.invalid` subscription addresses, unusable passwords, and the two-date activity split in both the raw seed and a materialized workspace.

The shared GitHub Actions `Test` job also runs Ruff, the shared Django suite, PostgreSQL 17, demo migrations, seed building, and this isolated suite. The PostgreSQL capacity test is intentionally not equivalent to the local SQLite run.

## Scope

There are no DRF/API tests because no API exists. This document covers the
focused backend and Django request tests; live deployment checks are separate
operational work.
