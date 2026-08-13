# Demo backend and web implementation

## Runtime boundary

The feature is implemented in `apps/vanta_demo/` and selected through:

- settings: `config/settings/demo.py`
- seed-build settings: `config/settings/demo_seed.py`
- URLconf: `config/demo_urls.py`
- app URLconf: `apps/vanta_demo/urls.py`
- default admin site: `apps.vanta_demo.admin.demo_admin_site`

The normal local/production settings do not install this runtime. `config/settings/__init__.py` preserves explicit `config.settings.demo` and `config.settings.demo_seed` selection. The demo pins a released Vanta Admin package in its dependency metadata.

## Request and database flow

`SessionMiddleware` runs before `DemoWorkspaceMiddleware`, which runs before `AuthenticationMiddleware`. The middleware reads only the server-created browser and workspace identifiers from the session, loads control state from `default`, validates status/version/file/path, registers a transient SQLite alias, sets a request-scoped `ContextVar`, and closes the workspace connection after the response. SQLite busy/locked read requests get one bounded retry; persistent contention becomes a private `503` state.

`DemoWorkspaceRouter` sends `sessions` and `vanta_demo` to `default`, and sends `admin`, `auth`, `contenttypes`, `demo_content`, `demo_projects`, `demo_newsletter`, `demo_status`, and `demo_contact` to the current workspace alias. Workspace models are denied when no alias is active; cross-database relations are denied. Workspace files are derived from UUIDs and constrained under `VANTA_DEMO_WORKSPACE_ROOT`.

## Admin and forms

`DemoAdminSite` requires a validated workspace plus an active staff user. It registers an explicit subset of auth, blog, project, newsletter, status, and contact models. Integration-only records and actions remain absent. `DemoAdminMixin` owns the record cap, workspace database selection for related fields, and demo-specific success messages. Individual admins configure representative 10-row pagination, search, filters, ordering, relations, and safe local actions. `DemoInlineMixin` owns bounded inline counts and workspace database selection.

`DemoUserForm` removes password editing, protects the synthetic `demo-admin`, and assigns unusable passwords to created users. Blog, project, and newsletter image forms expose URL-backed demonstration metadata without file inputs; multipart requests are rejected by middleware. All demo text fields receive a server-side 5,000-character limit and matching HTML `maxlength`.

## Templates, assets, and browser behavior

The public pages use `vanta_demo/base.html`, `overview.html`, `reset.html`, and `state.html` with `demo.css` and `demo.js`. The admin overrides `admin/base_site.html` and `vanta_demo/admin/index.html`, adds the persistent demo notice, and loads the existing Vanta theme assets plus `admin-demo.css` and `admin-demo.js`. No HTMX, Alpine.js, WebSocket, or frontend framework is used.

The public page is semantic, English-first, responsive, light/dark aware through existing site/theme tokens, and includes a skip link, labelled main content, focus styling, translated template strings, and external-link `rel` attributes. Live accessibility and viewport checks remain a browser-test gap.

## Configuration

Required runtime values are `DJANGO_SECRET_KEY`, `DATABASE_URL`, and `VANTA_DEMO_HASH_SECRET`. `DJANGO_SETTINGS_MODULE` must be `config.settings.demo`. The runtime also expects exact allowed hosts/origins and a readable seed plus writable workspace root.

Defaults defined in `config/settings/demo.py` include a 7,200-second idle TTL, 100 active/creating workspace capacity, five start/reset attempts per 600-second window, a five-second SQLite timeout, one-minute activity refresh throttling, a 300-second creating timeout, a 900-second orphan age threshold, a 60-second retry response, and a 100-record per-model cap. Deployment-specific values belong in the deployment environment, and secret values must never be added to this repository.

## Build and deployment integration

The Docker build creates a deterministic read-only seed under `/app/demo-seed/` and collects demo static files. Its seed filename must use the same `VANTA_DEMO_SEED_VERSION` as runtime settings; a focused test protects that image/runtime contract. The seed build places admin-history rows on two relative dates for representative dashboard activity. During workspace materialization, those timestamps are refreshed to the current configured project timezone, preserving the two-day split for visitors regardless of the calendar date. The container runs the demo-tagged Django checks, applies migrations, and starts Gunicorn with bounded worker/request defaults when `DJANGO_SETTINGS_MODULE=config.settings.demo`.

The cleanup command should run on a regular schedule. The deployment architecture requires one demo replica with a persistent `/app/demo-workspaces` volume, a dedicated PostgreSQL resource, no public database port, and recreate deployment rather than two containers sharing the workspace volume.

## Limitations

- Workspace SQLite files are local persistent-volume state; horizontal scaling and shared replicas are not supported.
- Workspace edits are intentionally disposable and are not backed up for user recovery.
- The demo does not expose public content, credentials, uploads, outbound email, analytics, or an API.
- Startup migrations are safe only under the documented single-container/recreate deployment invariant.
