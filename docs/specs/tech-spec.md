# Vanta Admin Interactive Demo Technical Specification

## Summary

Build the interactive Vanta Admin demo as a standalone Django runtime in its own repository. It runs with demo-specific settings, URLs, database routing, and a separate Coolify application at `demo.vanta-admin.org`.

Each browser receives a private, temporary workspace. Control data such as sessions, workspace leases, capacity, and throttling lives in a dedicated PostgreSQL database. The editable example admin data lives in one SQLite database file per workspace. Workspace files are copied from a versioned, deterministic seed and stored on a persistent volume until they expire or are reset.

This separation is intentional. Installing Vanta's `admin/...` templates in the main runtime could alter the shared production admin, while routing demo models through the main database could expose real application data. A separate runtime gives the demo an explicit allowlist and fail-closed database boundary while consuming the released Vanta package and owning its deployment assets.

The demo must pin a released `vanta-admin` package so its runtime cannot drift independently of the package it consumes.

## Source Product Spec

- Source: [`product-spec.md`](./product-spec.md)
- Product area: Vanta Admin public website
- Public host: `https://demo.vanta-admin.org/`
- Theme version: the released package selected in the demo dependency metadata.
- This technical specification resolves implementation details only. If user-facing behavior changes, update the product spec first.

## Scope

### In scope

- A public, indexable overview at `demo.vanta-admin.org`.
- One-click entry into a synthetic Vanta Admin workspace without account registration.
- Private browser-bound workspaces with seeded users, groups, blog posts, publications, projects, translations, and admin history.
- Realistic Django admin browsing, searching, filtering, pagination, creation, editing, deletion, and inline-form behavior.
- Vanta theme controls, responsive navigation, dashboard behavior, and activity/history views.
- Workspace start, reuse, reset, expiry, cleanup, capacity, and request-throttling behavior.
- Dedicated demo settings, URL configuration, admin site, database router, middleware, services, templates, static assets, tests, and deployment configuration.
- English-first, translation-ready interface copy.
- Public-page metadata, robots behavior, sitemap entry, privacy link, and no-index handling for non-public states.
- A separate Coolify application, database, persistent workspace volume, scheduled cleanup, health checks, and deploy trigger.

### Out of scope

- Changes to the Vanta theme package itself.
- A native mobile app or public API.
- Sharing data between browsers or preserving workspace data indefinitely.
- User registration, email, password authentication, two-factor setup, file uploads, external integrations, webhooks, or outbound messages.
- Public rendering of content created inside the demo admin.
- Analytics, advertising, behavioral tracking, or marketing cookies on the demo host.
- Horizontal scaling, multi-region operation, or multiple demo replicas.
- A public API, DRF endpoints, HTMX, Alpine.js, WebSockets, Celery, or Redis.
- Importing or copying data from the production `my-apps` database.

## Assumptions

- The demo is implemented under `apps/vanta_demo/`, with its own Django `AppConfig` and migrations label.
- `demo.vanta-admin.org` routes to a separate Coolify application and database from the main websites.
- The demo uses its own PostgreSQL database. It never receives credentials for the main `my-apps` database.
- One Coolify replica is a deployment invariant because workspace SQLite files are stored on a locally mounted persistent volume.
- Workspace data is disposable. Losing active workspaces during recovery is acceptable; the seed can recreate all example data.
- An inactive workspace expires after two hours by default. Capacity, lifetime, throttling, and record caps are environment-configurable without changing product behavior.
- The browser identity is represented by an essential Django session cookie. Workspace identifiers are not exposed in URLs or editable form values.
- The current product spec explicitly requires the small `Live demo` lead-in. Implement that copy on this page only; it does not establish a reusable eyebrow-label pattern for the rest of the site.
- The overview follows the browser's light/dark preference. Vanta's in-admin appearance preferences continue to use its existing browser-local behavior.
- The dedicated demo is English-only at launch, but all newly introduced interface strings use Django translation primitives.
- The existing Vanta privacy page remains the canonical privacy destination.
- Existing active workspaces may be expired after a deploy when the seed schema or version changes.

## Companion Skills

The following project skills govern implementation and review:

- `project-router`: confirm the implementation and review route before work begins.
- `python-guidelines`: services, typing, configuration, error handling, logging, and maintainability.
- `django-guidelines`: settings, middleware, URLs, forms, admin, migrations, and tests.
- `database-guidelines`: control models, constraints, indexes, transactions, workspace routing, and cleanup.
- `html-css-guidelines`: semantic server-rendered pages, responsive layout, forms, and minimal JavaScript.
- `locale-guidelines`: gettext-ready copy and locale behavior.
- `seo-guidelines`: canonical metadata, indexability, sitemap, robots, and social metadata.
- `deploy-python-vps`: Coolify application, database, storage, health checks, secrets, deployment, and recovery.

The implementation handoff must also use `write-tests` for focused Django coverage and `write-playwright-tests` for browser isolation and interaction coverage. Before release, use `review-web`, `review-config`, `review-migrations`, `review-performance`, `review-accessibility`, and `review-seo` as applicable.

## Technical Approach

### Architecture and ownership

Keep the feature within the existing repository and Vanta site boundary:

```text
apps/vanta_demo/
├── admin.py
├── admin_apps.py
├── apps.py
├── context.py
├── database.py
├── forms.py
├── management/commands/
├── middleware.py
├── migrations/
├── models.py
├── services/
├── static/vanta_demo/
├── templates/vanta_demo/
├── tests/
├── urls.py
└── views.py

config/
├── demo_urls.py
└── settings/
    ├── demo.py
    └── demo_seed.py
```

`apps.vanta_demo` is the standalone runtime app rather than a reusable theme component. It owns demo control records and runtime behavior. `apps.demo_content`, Django auth, and Django admin models provide the editable sample domain.

Run the feature through `config.settings.demo` and `config.demo_urls`. Do not add the Vanta package or demo middleware to the normal local/production settings. This prevents template, static-file, middleware, admin-site, and database-router behavior from affecting the shared production admin.

The existing `demo.vanta-admin.org` host recognition in `apps.core` remains a fail-closed fallback for an incorrectly routed request. The interactive routes exist only in the dedicated demo URL configuration. Coolify and Cloudflare must route the public demo hostname to the demo service, not the main service.

### Dependencies and settings

- Add and lock the selected released `vanta-admin` package in `pyproject.toml` and `uv.lock`.
- Keep the package absent from the main runtime's `INSTALLED_APPS`.
- In demo settings, order app template discovery so project overrides are found before the packaged Vanta templates, and Vanta templates are found before Django admin templates.
- Use a demo-specific `AdminConfig.default_site` pointing to `DemoAdminSite`.
- Set `ROOT_URLCONF = "config.demo_urls"`.
- Set a separate `STATIC_ROOT`, for example `/app/demo-staticfiles`.
- Use the existing WhiteNoise storage approach for immutable static assets.
- Set secure production cookies, `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"`, and a demo-specific cookie name.
- Set `LANGUAGES` to English only at launch while retaining `LocaleMiddleware` and gettext-ready source strings.
- Do not install or mount the project's OTP/two-factor admin configuration in the demo runtime.
- Do not include the main Vanta site's broad context processors if they query production-oriented blog/project content. Add a narrow demo metadata context where needed.
- Update `config/settings/__init__.py` so an explicit `DJANGO_SETTINGS_MODULE=config.settings.demo` or `config.settings.demo_seed` is not replaced by local settings.
- Update production-setting detection in base configuration so demo builds receive production-safe defaults without inheriting the main database.

Proposed demo environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | Yes | — | `config.settings.demo` |
| `SECRET_KEY` | Yes | — | Django signing and session security |
| `DATABASE_URL` | Yes | — | Dedicated demo control PostgreSQL database |
| `ALLOWED_HOSTS` | Yes | `demo.vanta-admin.org` | Accepted demo hostnames |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://demo.vanta-admin.org` | HTTPS form origin |
| `VANTA_DEMO_WORKSPACE_ROOT` | No | `/app/demo-workspaces` | Mounted workspace directory |
| `VANTA_DEMO_WORKSPACE_TTL_SECONDS` | No | `7200` | Idle workspace lifetime |
| `VANTA_DEMO_MAX_WORKSPACES` | No | `100` | Active plus creating capacity |
| `VANTA_DEMO_START_LIMIT` | No | `5` | Starts/resets per client window |
| `VANTA_DEMO_START_WINDOW_SECONDS` | No | `600` | Throttle window |
| `VANTA_DEMO_HASH_SECRET` | Yes | — | HMAC key for transient client buckets |
| `VANTA_DEMO_TRUSTED_IP_HEADER` | No | `HTTP_CF_CONNECTING_IP` | Trusted edge client-IP source |

The image owns the read-only seed path and seed version. They are updated with
the Vanta release and are intentionally not Coolify environment variables.

Validate integer values and filesystem paths at startup. Fail startup on an absent hash secret, missing/unreadable seed, a workspace root outside the configured path, or an unsupported theme/seed version.

### Control data model

Create control models in the nested demo app. All control models always use the dedicated PostgreSQL `default` database.

#### `DemoWorkspace`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | UUID primary key | Server generated; also forms the derived filename |
| `browser_id` | UUID | Stored in the Django session; never supplied by a form |
| `status` | choices | `creating`, `active`, `expired`, `failed`, `retired` |
| `seed_version` | short string | Must match the configured seed version |
| `created_at` | datetime | Database default/current time |
| `last_activity_at` | datetime | Throttled updates, at most once per minute |
| `expires_at` | datetime | Indexed absolute idle-expiry boundary |
| `retired_at` | nullable datetime | Cleanup/audit aid |
| `failure_code` | blank short string | Stable internal category; no exception text |

Constraints and indexes:

- A partial unique constraint permits only one `creating` or `active` workspace per `browser_id`.
- Index `(status, expires_at)` for capacity and cleanup scans.
- Index `(browser_id, status)` for session lookup.
- Do not store a client-controlled or absolute file path. Derive `<workspace-root>/<workspace-uuid>.sqlite3`, resolve it, and verify that it remains under the configured root.

#### `DemoThrottleBucket`

| Field | Type | Notes |
| --- | --- | --- |
| `key_hash` | fixed string | HMAC of normalized client address; never raw address |
| `action` | choices | Initially `workspace_start` |
| `window_started_at` | datetime | Fixed-window boundary |
| `count` | positive integer | Atomically incremented |
| `expires_at` | datetime | Indexed cleanup boundary |

Use a unique constraint on `(key_hash, action)`. Lock the bucket row during updates. Delete expired buckets in the cleanup command.

#### `DemoCapacityLock`

Use a singleton row as an explicit transaction lock during capacity reservation. Inside `transaction.atomic()`, lock it with `select_for_update()`, expire stale reservations, count `creating` plus `active` workspaces, and reserve the next row only when below the configured maximum. Do not rely on an unlocked count followed by an insert.

No control model has a foreign key to a workspace user or to any main-site model.

### Workspace database and routing

Each workspace is a private SQLite file copied from an immutable seed bundled into the image.

- The seed contains only migrations and deterministic fictional fixtures.
- Include Django auth, content types, admin log entries, blog models, project models, and their relationships.
- Create one synthetic `Demo Admin` superuser with an unusable password.
- Give every fictional user an unusable password.
- Seed enough rows to show filters, search, inlines, history, and at least two list pages with a demo list size of 10.
- Use fixed fixture values and timestamps relative to the seed build so image builds remain reproducible.
- Do not read the normal application database while building the seed.

Add `build_vanta_demo_seed`, a deterministic management command used by `config.settings.demo_seed`. It creates a new temporary SQLite database, applies only workspace-app migrations, loads fixtures, validates the expected synthetic administrator and schema, then atomically places the finished file in an image-owned directory. It must refuse to overwrite an existing destination unless an explicit build-only flag is provided.

Add a `DemoWorkspaceRouter` with strict allowlists:

- Route `sessions` and `vanta_demo` control models to `default` PostgreSQL.
- Route `auth`, `contenttypes`, `admin`, and `demo_content` reads/writes to the current workspace alias when a workspace context is active.
- Allow migrations for control apps only on `default`.
- Allow migrations for workspace apps only on seed/workspace aliases.
- Return a denial for an allowlisted workspace model when no active workspace exists; never fall back to `default`.
- Reject cross-database relations.

`DemoWorkspaceMiddleware` runs after `SessionMiddleware` and before `AuthenticationMiddleware`. It:

1. Reads the server-created `browser_id` and workspace ID from the session.
2. Loads the workspace row explicitly from `default`.
3. Rejects an inactive, expired, mismatched-version, or missing-file workspace.
4. Derives and validates the SQLite path.
5. Registers the workspace alias with `CONN_MAX_AGE = 0` and a bounded SQLite busy timeout.
6. Sets a request-scoped `ContextVar` used by the database router.
7. Clears the context and closes the workspace connection after the response.

Aliases may remain registered for the lifetime of a worker because removing a shared alias could race with another request. Configure Gunicorn `max_requests` and `max_requests_jitter` to bound alias growth. Keep SQLite's simple journal behavior and treat brief write contention as a recoverable user-facing error. Multiple tabs in the same browser may share one workspace.

Use a dedicated `DemoWorkspaceBackend` for session user loading. It accepts no credentials and resolves users only while a validated workspace context is active. After creating or replacing a workspace, enter that context, load the protected synthetic administrator, and call Django's `login()` with the dedicated backend. Expiry and unrecoverable workspace failure clear the authentication session before showing the public state. This keeps normal Django admin permission checks intact without exposing a credential-based login path.

### Workspace lifecycle services

Implement lifecycle behavior in small transaction-aware services, not in views or middleware.

#### Start or resume

1. The overview GET ensures a Django session exists and stores a short-lived start marker.
2. The start POST requires the marker from the same session. A request that did not return the session cookie is rejected before reserving capacity.
3. Normalize the trusted client address and HMAC it immediately for the throttle lookup.
4. If the browser already has a valid active workspace, refresh its idle expiry and redirect to `/admin/`.
5. Under the capacity lock, reserve a `creating` row.
6. Copy the seed to a temporary filename under the workspace root, set restrictive permissions, and atomically rename it to the derived final path.
7. Mark the workspace active, save its ID in the session, sign in the seed's synthetic administrator through `DemoWorkspaceBackend`, and redirect to `/admin/`.
8. On failure, remove only the derived temporary/final files, mark the row failed with a stable code, and show the unavailable state.

#### Activity and expiry

- Workspace-authenticated admin requests refresh `last_activity_at` and `expires_at` at most once per minute.
- A workspace past `expires_at` is marked expired, detached from the session, and redirected to `/expired/`.
- A seed-version mismatch is handled as expiry so old schemas are never used with new code.
- A missing or invalid workspace file is handled as failure/expiry. It must never result in a query against `default`.

#### Reset

- GET `/reset/` renders a confirmation page.
- POST `/reset/` applies the same session validation and throttle as start.
- Reserve and fully create a replacement workspace before retiring the current one.
- Switch the session to the replacement and sign in its synthetic administrator only after the new file is ready.
- Retire and remove the old workspace afterward. If replacement creation fails, preserve the existing workspace and show a retryable error.

#### Cleanup

Add an idempotent `cleanup_vanta_demo_workspaces` management command:

- Lock and expire stale `creating` reservations.
- Mark idle or seed-mismatched workspaces expired.
- Remove files only after resolving and verifying their derived paths.
- Retire failed and expired rows after file removal.
- Remove orphan files whose UUID has no live control row after a conservative age threshold.
- Delete expired throttle buckets.
- Emit aggregate structured logs only: counts, durations, and stable failure categories.
- Support `--dry-run` and a bounded `--limit`.
- Return non-zero on an incomplete cleanup pass caused by an operational error.

The command runs every five minutes as a Coolify scheduled task. It must be safe to overlap, though the production schedule should avoid intentional overlap.

### Demo admin site

Create a dedicated `DemoAdminSite`; do not reuse `apps.core.admin_site` or the OTP-protected production admin.

- Set product-specific `site_header`, `site_title`, and `index_title` values.
- Use a demo-specific dashboard template extending the Vanta base.
- Require both an active workspace and an active/staff workspace user in `has_permission()`.
- Register only the allowlisted demo model admins.
- Do not autodiscover or register the repository's status, contact, site-content, or infrastructure-related models.
- Reuse the activity-log admin mixin only if it reads the current workspace-routed `LogEntry` table and introduces no dependency on the main database.

Allowlisted demonstrations:

- Users and groups, including group many-to-many controls.
- Blog posts with translation and publication relationships/inlines.
- Projects with translation relationships/inlines.
- Django object history and recent admin activity.

Demo-specific `ModelAdmin` classes must:

- Use search fields, filters, ordering, date hierarchy, fieldsets, inlines, and list size 10 where they help demonstrate Vanta.
- Apply conservative per-model record caps through `has_add_permission()` and form/formset validation.
- Apply bounded form lengths for editable text values even where the reusable model field has no tight maximum.
- Keep selects and querysets scoped to the workspace alias.
- Set unusable passwords for newly created fictional users and omit password-entry/change controls.
- Prevent deletion, deactivation, demotion, or permission changes to the synthetic `Demo Admin` account.
- Protect the synthetic account in single-object and bulk-delete paths.
- Preserve ordinary create/edit/delete behavior for non-protected seeded records.
- Avoid file fields and any action that sends email, invokes a webhook, or touches an external service.

Do not expose credential-based login, password-change, two-factor, or account-recovery flows. Override the `DemoAdminSite` login, logout, password-change, and password-change-done handlers so direct requests redirect safely to the overview or reset flow without showing their normal forms. The visible account menu should link back to the overview and reset confirmation with demo-specific labels. Prefer a small project template override plus minimal plain JavaScript over copying the packaged navigation template. Server routes remain authoritative if JavaScript is unavailable.

### URLs and response behavior

Use unprefixed canonical routes on the dedicated host:

| Method | Route | Behavior | Indexing |
| --- | --- | --- | --- |
| GET | `/` | Public overview and start form | `index,follow` |
| POST | `/start/` | Resume or create workspace | `noindex` |
| GET | `/reset/` | Reset confirmation | `noindex,noarchive` |
| POST | `/reset/` | Replace current workspace | `noindex,noarchive` |
| GET | `/expired/` | Expired-workspace explanation and new-start action | `noindex,noarchive` |
| GET/POST | `/admin/...` | Dedicated demo admin | Vanta admin no-index policy |
| GET | `/robots.txt` | Demo-specific crawler policy | Plain text |
| GET | `/sitemap.xml` | Contains only canonical overview URL | XML |
| GET | `/healthz/` | Process liveness; no workspace creation | `noindex` |
| GET | `/readyz/` | Control DB, seed, and volume readiness | `noindex` |
| GET | `/favicon.ico` | Existing Vanta favicon | Asset |

Additional behavior:

- Never place browser or workspace IDs in a route, query string, form field, log line, or page source.
- Use POST plus CSRF protection for start and reset mutations.
- Direct `/admin/` access without an active workspace redirects to `/` with a short state code, not sensitive detail.
- Return `429` with `Retry-After` for a throttle response.
- Return `503` with `Retry-After` for capacity or temporary workspace-service failure.
- Keep the root overview response at `200`; do not vary its visible content by active workspace so it remains predictable to crawlers and caches.
- Send `Cache-Control: no-store, private` on session-mutating and workspace/admin responses. Public overview HTML may use a short shared-cache policy only if the response does not set or depend on a session; otherwise use private revalidation.

### Templates, styling, and JavaScript

Update the existing demo overview rather than creating a second visual direction.

- Reuse Vanta site's self-hosted fonts, logo, favicon, social preview, design tokens, and public layout conventions.
- Follow the shared Vanta style: compact admin-first composition, clear surface contrast, borders instead of decorative depth, dark background around `#111213`, and the established green/dark and blue/light accents.
- Render the product-spec title, explanation, persistence warning, feature highlights, `Try the demo` action, version note, documentation link, and privacy link.
- Remove the work-in-progress and no-index state from the public overview.
- Do not include the site's Plausible partial or another analytics script on the demo host.
- Use a normal server-rendered reset confirmation page rather than a modal.
- Add an always-visible compact demo notice inside the admin explaining that changes are private and temporary, with links to reset and return to the overview.
- Keep failure, expiry, cookie-required, rate-limit, capacity, and reset states inside the same visual system.
- Give submitted buttons a disabled/busy state. The server must remain correct without JavaScript.
- Use minimal plain JavaScript only for progressive busy-state feedback and adapting demo-specific account-menu labels/links when the packaged template lacks a suitable block.
- Do not add a frontend framework or a new asset build tool.

### Locale behavior

- Use `gettext`/`gettext_lazy` in Python and `{% translate %}`/`{% blocktranslate %}` in templates for every new user-facing string.
- Launch with English only and no locale prefix so `/` remains the specified canonical URL.
- Do not infer locale from client address.
- Preserve correct `lang`, title, form label, error, and metadata values.
- A future language launch must define translated canonical URLs and `hreflang` together; do not emit incomplete alternates now.
- Seed fixture text is fictional demo data and may remain English for this launch.

### SEO and social metadata

- Set the public title to `Vanta Admin Demo | Try the Django Admin Theme`.
- Use the product-spec description and canonical `https://demo.vanta-admin.org/`.
- Emit matching Open Graph and Twitter Card metadata with the existing absolute Vanta preview image.
- Include only the overview in the demo sitemap.
- Disallow `/admin/`, `/start/`, `/reset/`, and `/expired/` in the demo robots response.
- Set `X-Robots-Tag: noindex, noarchive` on reset, expired, capacity, throttle, error, health, and readiness responses.
- Keep Vanta's existing no-index behavior on admin pages.
- Do not reuse the main Vanta sitemap or generate blog/project URLs on the demo host.

### Privacy and security boundaries

- The demo service receives no main-database URL, production admin cookie, email credentials, object-storage credentials, webhook credentials, or unrelated API keys.
- Use a demo-specific session cookie name and signing secret so sessions are not portable between hosts.
- Trust `CF-Connecting-IP` only when the deployment guarantees all public traffic reaches the service through the configured Cloudflare/Traefik path. Fall back to the direct peer address in local development.
- HMAC the normalized address immediately. Retain only the bucket hash and window counters, then delete expired buckets.
- Set request-body limits at the edge and Django layer. Do not accept multipart uploads.
- Use restrictive file and directory permissions for seed/workspace SQLite files.
- Resolve all delete/copy targets under the configured workspace root. Never accept a filesystem path from a request.
- Exclude form values, session keys, cookies, workspace IDs, client addresses, SQL, and exception representations containing submitted data from application logs.
- Use stable error codes and aggregate operational metrics only.
- Keep Django's CSRF, clickjacking, secure-cookie, HTTPS redirect, host validation, and security-header settings enabled in production.
- Ensure all template output uses Django's normal escaping; do not introduce `safe` for editable values.
- No public URL renders workspace blog or project records.
- Capacity and rate checks supplement, but do not replace, infrastructure request limits and resource limits.

### Errors and operational states

Map internal failures to stable user states:

| Condition | Response | User action |
| --- | --- | --- |
| Session cookie absent on start | `400` cookie-required page | Enable essential cookies and retry |
| Start/reset limit exceeded | `429`, `Retry-After` | Wait and retry |
| Workspace capacity reached | `503`, `Retry-After` | Retry later |
| Seed missing or unreadable | `503` unavailable page | Retry later; alert operator |
| Copy/activation failure | `503` unavailable page | Retry; preserve old workspace on reset |
| Workspace expired/version changed | Redirect to `/expired/` | Start a fresh workspace |
| Workspace file missing/corrupt | Expire then show safe unavailable/expired state | Start fresh |
| SQLite temporarily busy | Retry once where transaction-safe, then friendly error | Retry the action |
| Unexpected exception | Standard demo 500 page with request ID | Retry; operator checks redacted logs |

Readiness fails if PostgreSQL is unavailable, the seed is missing/unreadable, or the mounted workspace root is absent/unwritable. Liveness only confirms that the Django process can respond and must not create a session or query a workspace.

### Performance and resource limits

- Use one application replica and a small fixed Gunicorn worker count appropriate to the VPS.
- Configure Gunicorn request recycling to bound dynamic database aliases.
- Keep `CONN_MAX_AGE = 0` for workspace aliases.
- Update workspace activity no more than once per minute per active workspace.
- Paginate admin lists at 10 and cap fixture/query sizes.
- Add database indexes described in the control model section.
- Keep cleanup batches bounded and observable.
- Set CPU, memory, and process limits in Coolify. Capacity should be tuned below the point where workspace files or concurrent SQLite writes pressure the host.
- Use WhiteNoise-compressed static assets and existing self-hosted fonts; do not add remote runtime assets.

### Accessibility

- Preserve Vanta's semantic admin templates, keyboard navigation, focus treatment, labels, help text, errors, and responsive navigation.
- Use a heading-led overview and state pages with one clear primary action.
- Announce server-side errors next to their related form and in an error summary where applicable.
- Ensure busy-state JavaScript does not remove the accessible button name and does not trap focus.
- Do not rely on color alone for demo, expiry, rate-limit, capacity, or error states.
- Keep touch targets, contrast, zoom/reflow, mobile tables/forms, and reduced-motion behavior within the existing Vanta standards.
- Test the dashboard, changelists, change forms, inlines, account menu, reset flow, and failure pages with keyboard-only navigation and narrow viewports.

### Deployment and operations

Create the dedicated Coolify application from the standalone `vanta-demo` repository/image. Use the existing private GitHub Actions-to-Coolify deployment path with the repository's protected deploy URL/token, triggering it only after the standalone test job succeeds.

- Attach only `demo.vanta-admin.org` to the demo service.
- Provision a dedicated PostgreSQL database and inject only its URL.
- Mount a persistent volume at `/app/demo-workspaces`. Coolify documents that persistent storage survives deployments and mounts at a destination path inside the container: [Persistent Storage](https://coolify.io/docs/knowledge-base/persistent-storage).
- Do not mount the seed path; keep the seed in the immutable image.
- Build both main and demo static collections in the image, and build/validate the demo seed after dependencies and source are copied.
- Start the demo with its own settings module. While the deployment is constrained to one replica, the start command may run control migrations before Gunicorn, matching the repository's current startup convention.
- Configure the health check against `/readyz/` and retain `/healthz/` for process diagnosis.
- Configure `cleanup_vanta_demo_workspaces` every five minutes using a Coolify scheduled task; standard cron expressions are supported: [Supported Cron Syntax](https://coolify.io/docs/knowledge-base/cron-syntax).
- Set conservative CPU/memory limits and alert on readiness failures, repeated cleanup failures, high capacity, workspace-creation failures, and disk usage.
- Remove `demo.vanta-admin.org` from the main application's proxy domains once the demo service is healthy, while retaining a fail-closed application fallback.
- Keep the origin inaccessible directly and preserve the existing Cloudflare/Tailscale deployment boundary.
- Do not back up workspace files. The control database is also disposable; recovery consists of redeploying, recreating control tables, and letting browsers start fresh.

Deployment order:

1. Build and validate the image, static files, migrations, and seed.
2. Provision the dedicated PostgreSQL database and workspace volume.
3. Deploy the demo service without public traffic and run readiness checks.
4. Verify that its environment has no main-service credentials.
5. Route `demo.vanta-admin.org` to the demo service.
6. Run smoke tests in two isolated browser contexts.
7. Enable the cleanup schedule and operational alerts.
8. Remove the demo domain from the main service's proxy configuration.

Rollback routes the hostname to a maintenance response or the previous healthy demo image. Active workspaces may be discarded. Never route the interactive host to the main production database as a rollback mechanism.

### Automated test strategy

Use ordinary Django tests for deterministic boundaries and Playwright for browser/session behavior.

Focused Django coverage must include:

- Control-model constraints, indexes, state transitions, and expiry calculations.
- Atomic capacity reservation under concurrent attempts.
- Fixed-window throttle increments and expiry without retaining the raw address.
- Seed build determinism and expected model/user/log fixtures.
- Workspace copy, activation, failure cleanup, reset replacement, and old-workspace preservation on failed reset.
- Derived-path containment and rejection of missing/corrupt workspace files.
- Database-router decisions for every allowed app and explicit denial without a workspace context.
- Middleware ordering, context cleanup, session ownership, synthetic-admin sign-in, credential rejection, seed-version mismatch, and no fallback to `default`.
- Cleanup idempotency, dry run, bounded batches, stale reservations, and orphan-file handling.
- Admin model allowlist, synthetic-admin protections, record caps, unusable passwords, search/filter/pagination, and history routing.
- Start/reset CSRF, cookie marker, response codes, `Retry-After`, and cache/no-index headers.
- Public metadata, canonical URL, robots response, sitemap contents, and absence of analytics scripts.
- Health/readiness behavior without workspace creation.
- English locale and translation extraction for newly added copy.

Playwright scenarios should remain focused to roughly six end-to-end stories:

1. Start the demo, browse dashboard/model lists, create/edit/delete a record, and see workspace history.
2. Use two clean browser contexts; confirm a change in one never appears in the other.
3. Reset one browser's workspace and confirm both its seed state and the other browser's unchanged state.
4. Exercise Vanta light/dark, font, time, and sidebar preferences, then reload and verify browser-local persistence.
5. Verify expired, capacity, throttle, and essential-cookie states with controlled test configuration.
6. Exercise keyboard navigation and a mobile viewport across overview, dashboard, changelist, form/inlines, account menu, and reset confirmation.

Tests must use temporary directories and temporary databases. They must never read or write the developer's real demo volume or the main application database.

## Implementation Tasks

1. **Pin and isolate the released Vanta package**
   - Add the selected released `vanta-admin` version and update the lockfile.
   - Add demo/demo-seed settings and explicit settings-package dispatch.
   - Confirm normal local and production settings do not install Vanta or demo runtime components.

2. **Create the nested demo control app**
   - Add `apps.vanta_demo` with `DemoWorkspace`, `DemoThrottleBucket`, and `DemoCapacityLock`.
   - Add constraints, indexes, migrations, Django system checks, and admin-free control ownership.
   - Document the environment settings and defaults in the feature docs/config sample.

3. **Build the deterministic seed pipeline**
   - Add `config.settings.demo_seed` and `build_vanta_demo_seed`.
   - Register only the workspace model set for seed migrations.
   - Add fictional fixtures, synthetic users with unusable passwords, relations, and admin logs.
   - Validate deterministic output and the seed contract during image build.

4. **Implement workspace routing and middleware**
   - Add the request `ContextVar`, strict database router, path resolver, dynamic alias registration, and connection cleanup.
   - Add session-to-workspace middleware before authentication.
   - Add tests proving workspace models cannot fall through to `default`.

5. **Implement lifecycle services and commands**
   - Add client-key hashing, throttle, capacity reservation, start/resume, activity refresh, expiry, reset, and failure cleanup services.
   - Add the idempotent cleanup command with dry-run/batch behavior.
   - Add structured, redacted operational logging.

6. **Create the dedicated demo admin**
   - Add `DemoAdminSite`, app allowlist, dashboard, activity/history behavior, and demo-only model admins/forms.
   - Protect the synthetic administrator in all edit/delete paths.
   - Add record caps, form limits, unusable-user-password behavior, and external-action exclusions.

7. **Implement demo routes and state views**
   - Add overview, start, reset, expired, error, robots, sitemap, favicon, health, and readiness routes.
   - Add CSRF, session-marker, status-code, `Retry-After`, cache, and no-index behavior.
   - Ensure login/password/two-factor/logout paths cannot open real account flows.

8. **Finish templates and assets**
   - Convert the current work-in-progress demo template into the specified overview.
   - Add admin notice/dashboard overrides and all state pages.
   - Reuse public Vanta styles/assets and add only scoped demo CSS and minimal plain JavaScript.
   - Remove analytics from the demo host and verify responsive/accessibility states.

9. **Update image and local-development workflows**
   - Collect demo static files and generate the seed during the Docker build.
   - Add a documented command for running the demo settings on a separate local port at `demo.vanta.localhost`.
   - Add temporary-directory defaults for tests and explicit startup checks.

10. **Add automated tests**
    - Use `write-tests` to implement the focused Django test matrix.
    - Use `write-playwright-tests` for the six browser stories.
    - Run the existing repository suite to prove the main sites/admin remain unchanged.

11. **Review before deployment**
    - Run the selected web, configuration, migration, performance, accessibility, and SEO reviews.
    - Verify the package/template ordering and database boundary against the built image.
    - Verify logs and error pages with representative editable values.

12. **Provision and release the demo service**
    - Create the dedicated Coolify application, PostgreSQL database, volume, secrets, limits, health check, and cleanup schedule.
    - Extend the existing private deploy workflow with a separate demo deploy target.
    - Follow the staged deployment order and two-browser smoke test.
    - Remove the demo hostname from the main service's proxy configuration after cutover.

## Manual Acceptance Criteria

- `https://demo.vanta-admin.org/` returns the specified public overview with correct title, description, canonical, social metadata, privacy/docs links, the installed Vanta release label, and no analytics request.
- The overview follows the browser's light/dark preference and remains usable at mobile, tablet, and desktop widths.
- Selecting `Try the demo` creates or resumes a workspace and opens the Vanta dashboard without registration or login.
- A browser with essential cookies disabled receives the cookie-required state before a workspace is created.
- The admin shows only the approved users/groups, blog, project, and activity/history areas.
- The synthetic `Demo Admin` cannot be deleted, deactivated, demoted, or stripped of required permissions through direct or bulk actions.
- A visitor can search, filter, paginate, create, edit, and delete ordinary example records, including inline/relationship controls.
- Vanta theme, font, time, and sidebar controls behave as expected and remain local to that browser.
- A change made in one clean browser profile is absent from a second clean browser profile.
- Reset requires confirmation, restores seeded data for the initiating browser, and leaves another browser's data unchanged.
- A failed reset leaves the current workspace usable.
- Expired workspaces show the specified state and can be replaced without exposing their identifier.
- Capacity and throttle tests return `503`/`429` with `Retry-After` and usable retry guidance.
- No workspace identifier, session value, client address, submitted form value, or workspace filesystem path appears in URLs, page source, or ordinary application logs.
- Direct demo login, password, two-factor, and account-recovery routes do not expose real authentication flows.
- No public demo URL renders a workspace's blog or project records.
- Reset, expiry, error, health, and admin responses are no-index; the sitemap contains only the public overview.
- `/readyz/` fails when the control database, seed, or workspace volume is unavailable, while `/healthz/` performs no workspace/database mutation.
- Cleanup expires old workspaces, removes their files, prunes throttle rows, handles orphan files, and produces the same result when safely rerun.
- The demo container has no main-database, email, object-storage, webhook, or unrelated service credentials.
- The main `my-apps` websites and OTP-protected admin retain their existing templates, settings, database behavior, routes, and tests.
- The deployed service runs one replica, uses the dedicated PostgreSQL database and mounted workspace volume, and executes the scheduled cleanup successfully.
- Keyboard-only and 200% zoom checks pass for the overview, dashboard, lists, forms/inlines, account menu, reset, and operational states.

## Open Questions

None. The defaults above are deliberate launch assumptions and remain configurable for tuning after measured use.
