# Demo database design

## Ownership split

The demo has two database layers:

1. Dedicated PostgreSQL `default` control database: Django sessions, workspace leases, capacity lock, and throttling.
2. One SQLite file per active browser workspace: fictional auth, content types, admin log, blog, project, newsletter, status, and contact data.

The main site's database is never a valid source or fallback for the demo. A workspace path is derived as `<workspace-root>/<workspace-uuid>.sqlite3`, resolved, and rejected if it escapes the configured root.

## Control models

### `DemoWorkspace`

Fields are UUID `id`, session-bound `browser_id`, `status`, `seed_version`, `created_at`, `last_activity_at`, `expires_at`, nullable `retired_at`, and a short `failure_code`. Status choices are `creating`, `active`, `expired`, `failed`, and `retired`.

The partial unique constraint `vanta_demo_one_live_workspace_per_browser` allows only one `creating` or `active` row per browser. Indexes cover `(status, expires_at)` for capacity/cleanup and `(browser_id, status)` for session lookup. `is_active()` requires active status, current seed version, and a future expiry.

### `DemoThrottleBucket`

Stores an HMAC-derived `key_hash`, action choice, fixed-window start, count, and indexed expiry. The `(key_hash, action)` uniqueness constraint supports atomic fixed-window rate limiting. Raw client addresses are not stored.

### `DemoCapacityLock`

A singleton row with primary key `1`. Workspace creation locks this row inside a PostgreSQL transaction before counting `creating` and `active` workspaces, preventing an unlocked check-then-insert race.

## Workspace file contents

The seed command applies only workspace-app migrations through the router and loads deterministic fictional data into a temporary SQLite file before atomically moving it into place. The file includes Django `auth`, `contenttypes`, and `admin` plus `demo_content`, `demo_projects`, `demo_newsletter`, `demo_status`, and `demo_contact`. Sessions and demo control records remain in PostgreSQL.

The seed contains 24 users including `demo-admin`, four permission groups, 60 blog articles, 12 authors, 30 blog images, 24 projects, 80 newsletter subscriptions, 24 campaigns, 80 delivery rows, 12 status monitors, 24 incidents with 48 updates, 60 contact messages, and 30 admin-history rows. Blog articles and projects include their English translation and relationship data. All passwords are unusable, all email addresses and asset links use reserved `.invalid` domains, and no workspace model exposes a file field.

Blog relations cover authors, categories, tags, images, comparisons, publications, translations, and related articles. Projects retain English translation rows. Newsletter records model sites, subscriptions, URL-backed images, campaigns, and deliveries without provider/email actions. Status records model pages, selected monitor services, incidents, affected services, and incident updates without Kuma fetching. Contact messages provide a safe local bulk mark-as-read action.

The seed's fixture timestamps remain deterministic, while its 30 admin-history rows are split across two relative dates. When a workspace is materialized, `_refresh_seed_activity()` rewrites those rows using the current configured project timezone so every fresh workspace has activity under both **Today** and **Yesterday**. The seed does not need to be rebuilt each day.

## Migrations and compatibility

`apps/vanta_demo/migrations/0001_initial.py` creates the control tables; `0002_seed_capacity_lock.py` creates the singleton lock. Workspace schema is built into the versioned seed. A seed-version mismatch expires existing workspaces instead of opening them with incompatible code.

Control migrations run on `default`; workspace migrations run only on a registered seed/workspace alias. Cross-database relations are denied. Cleanup removes expired/failed files only after path validation and is idempotent. Workspace content is disposable, so losing it during volume recovery is an accepted product consequence; recreate from the seed instead.

## Query/performance notes

Representative admin lists use 10 rows per page so the richer seed exercises normal pagination controls. Additions remain capped at 100 records per registered model, and inline formsets are capped at 20 rows. Workspace activity timestamps are refreshed at most once per configured interval. SQLite connections use `CONN_MAX_AGE=0` and a bounded busy timeout. The single-replica deployment invariant is required because workspace files are local volume state.
