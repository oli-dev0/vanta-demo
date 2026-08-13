# Demo web product behavior

## Verified public behavior

The overview template presents the live-demo label, installed Vanta Admin and Django runtime version labels, fictional-data warning, private temporary-workspace explanation, primary **Try the demo** action, Vanta website link, documentation link, privacy link, and a Vanta preview image. It is the only indexable page. The response has private/no-cache behavior and canonical, Open Graph, Twitter, and description metadata.

The start form is a CSRF-protected POST. It shows a busy label through the small demo JavaScript behavior and redirects a successful start to `/admin/`. The start path does not accept upload-like multipart requests.

## Verified admin behavior

The dedicated admin dashboard is labelled `Demo Admin`, displays seeded recent activity, and shows a persistent **Demo mode** notice with links to reset the workspace or return to the overview. Its explicit allowlist covers users and groups; blog articles, authors, categories, tags, images, comparisons, and related articles; projects; newsletter sites, subscriptions, images, campaigns, and deliveries; status pages, monitors, and incidents; and contact messages. Blog articles expose publication and translation inlines, projects expose translation inlines, status pages expose service inlines, and incidents expose update inlines. Representative long lists use 10 rows per page to exercise Vanta pagination, with search, filtering, and ordering configured per admin class.

Normal Django admin create, change, delete, search, filter, pagination, relationship, and history behavior is available inside the workspace. Success messages are rewritten to say that the change occurred in the demo workspace. Server-side demo limits cap text fields at 5,000 characters, inline formsets at 20 rows, and model additions at `VANTA_DEMO_MODEL_RECORD_CAP` records.

The Vanta theme continues to provide its browser-local appearance, font, time-format, sidebar collapse, width, open-section, and section-order preferences. A successful reset marks those preference keys for one-time localStorage removal on the next admin response.

## States and recovery actions

| State | Current response | User action |
| --- | --- | --- |
| Cookies missing | `400` | Return to the overview and enable essential cookies. |
| Rate limited | `429` with `Retry-After` | Wait and retry. |
| Capacity reached | `503` with `Retry-After` | Retry later. |
| Workspace unavailable | `503` | Retry later. |
| Workspace expired or seed version changed | Admin request redirects to `/expired/` | Start a new demo. |
| Invalid/missing workspace file | Fails closed, records `workspace_invalid`, and redirects to `/expired/` | Start a new demo. |
| CSRF, bad request, forbidden, not found, or server error | Private state page with `noindex`; server errors include a safe request reference | Return to the overview or retry as offered. |

Private state and admin responses use `no-store`/private cache behavior and `X-Robots-Tag: noindex, noarchive`. Admin login and password-change routes do not expose credential forms: login/logout return to the overview and password change returns to the reset flow.

## Acceptance status

- Implemented and covered by focused Django tests: session-bound start, capacity/rate-limit/error states, workspace isolation, reset, expiry, seed mismatch, missing-file fail-closed behavior, admin allowlist, protected synthetic user, preference reset marker, robots/sitemap behavior, health/readiness, deterministic seed, form limits, and cleanup.
- Implemented in templates and CSS but not covered by a Playwright spec in this repository: visual responsive behavior, keyboard interaction, theme controls, and browser busy-state behavior.

## Intentional differences from the product spec

The implemented dataset is concrete rather than generic: it contains Django auth records and related blog, project, newsletter, service-status, contact, and admin-history records. Newsletter delivery and status-monitor data is editable demonstration state only: the demo does not expose send, retry, preview, provider-fetch, webhook, upload, or other external-integration actions. There is no public rendering of workspace records, user registration, analytics, API, or mobile surface. These are deliberate scope boundaries, not missing API work.
