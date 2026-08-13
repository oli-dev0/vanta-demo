# API contract

No DRF, REST, GraphQL, or other public data API exists for this feature. The demo is served by normal Django views and Django admin HTML. No mobile client or third-party integration consumes a JSON contract.

## Browser routes

| Method | Path | Purpose | Access/cache behavior |
| --- | --- | --- | --- |
| `GET` | `/` | Indexable demo overview | Public page; private/no-cache response with indexable metadata. |
| `POST` | `/start/` | Start or resume the current browser workspace | Session marker and CSRF required; private/no-store; state errors are noindex. |
| `GET` | `/reset/` | Render reset confirmation | Uses the admin cancel link when a workspace is active, otherwise the overview; private/no-store. |
| `POST` | `/reset/` | Replace the current workspace with a fresh seed | Session marker and CSRF required; private/no-store. |
| `GET` | `/expired/` | Explain expired/disposable workspace | Private/no-store; noindex. |
| `GET` | `/robots.txt` | Allow only the overview to be crawled | Excludes admin and lifecycle paths. |
| `GET` | `/sitemap.xml` | Advertise the overview URL | Contains only `https://demo.vanta-admin.org/`. |
| `GET` | `/healthz/` | Cheap liveness response | Does not create a session or workspace. |
| `GET` | `/readyz/` | Check control DB, capacity lock, seed, and workspace volume | `200` when ready, `503` otherwise; private/noindex. |
| `GET` | `/favicon.ico` | Redirect to the shared Vanta favicon | Public static redirect. |
| `GET`/admin routes | `/admin/` | Standard Django admin HTML against the active workspace | Requires session-bound active workspace and synthetic staff user; private/no-store. |

The admin route set is supplied by `DemoAdminSite.urls`; it does not create a separate JSON response shape, pagination API, version header, or client compatibility promise. Query strings used by Django changelists remain normal admin UI inputs and are never treated as workspace identifiers.

## Errors and privacy

CSRF failures, invalid methods/content types, capacity/rate-limit failures, expiry, unavailable workspaces, and unexpected errors are converted to safe HTML state pages. Rate/capacity responses include `Retry-After` where appropriate. Server errors expose only a short request reference and log a category/reference, not workspace data or credentials.
