# Demo implementation decisions

## Separate runtime and database boundary

The demo uses `config.settings.demo` and `config.demo_urls` with a dedicated admin site and database router. This prevents Vanta package templates, demo middleware, admin registration, or sample queries from changing the main runtime or touching production data.

## PostgreSQL control data plus per-workspace SQLite

Lease, session, capacity, and throttle state needs shared transactional storage; editable fictional data needs hard per-browser separation and cheap recreation. The split provides both. The tradeoff is a one-replica/local-volume deployment invariant.

## Session-bound workspaces without URL IDs

The workspace UUID is stored in the server-side session and never accepted from a URL or form. This keeps copied links from becoming access tokens. A missing/mismatched session fails closed and returns the visitor to a safe public state.

## Seed version as compatibility boundary

Each workspace records `VANTA_DEMO_SEED_VERSION`. A mismatch expires the workspace rather than attempting a migration against a file made for another theme/schema version. This favors safe recreation over preserving disposable edits.

## Synthetic credential-free administrator

The seed contains a protected `demo-admin` with an unusable password. The custom backend only resolves that user within a validated workspace; login/password-change routes never expose credential flows. This preserves Django admin permission checks without creating a real account or credential surface.

## Explicit model allowlist and bounded edits

The registry includes only selected auth, blog, project, newsletter, status, and contact models that demonstrate useful admin patterns. File fields, production/admin infrastructure, outbound integrations, provider actions, webhooks, and unrelated application data remain unavailable. Text, inline, request-size, and record caps limit the resource impact of an intentionally public writable demo.

## Public overview only is indexable

The overview gets canonical/OG/Twitter metadata and is the only sitemap URL. Admin, lifecycle, state, and operational responses are private/no-store and noindex. This prevents temporary workspace content and diagnostics from becoming public search content.

## Deployment is recreate-only

Two containers must not serve the same local workspace volume or run startup migrations concurrently. The runbook therefore requires one demo container and recreate deployment. Horizontal scaling is deferred rather than hidden behind an unsafe shared-filesystem assumption.
