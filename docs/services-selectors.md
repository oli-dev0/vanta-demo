# Services and selectors

There are no separate selectors: workspace reads are owned by Django admin querysets and the current workspace database alias. The feature keeps lifecycle state changes in `apps/vanta_demo/services/workspaces.py` so views and middleware do not duplicate reservation, reset, expiry, file, or throttle rules.

## Service ownership

- `ensure_browser_session()` creates the server-side browser UUID in the session.
- `issue_start_marker()` and its validation bind start/reset POSTs to the same session that rendered the form.
- `start_or_resume_workspace()` resumes a valid active workspace or reserves, materializes, activates, and signs in a new one.
- `reset_workspace()` creates and signs in a replacement before retiring/removing the old workspace; failed replacement preserves the current workspace.
- `consume_start_throttle()` uses an HMAC-only client bucket and returns a retry interval on limit.
- `refresh_workspace_activity()` extends idle expiry at a bounded frequency.
- `validate_workspace_file()`, path helpers, and materialization enforce the seed/file boundary.
- `cleanup_vanta_demo_workspaces` expires stale rows, removes derived files/orphans/throttle buckets, supports `--dry-run` and bounded `--limit`, and logs aggregate counts.

## Permission and visibility rules

`DemoWorkspaceMiddleware` is the request boundary. It requires both session identifiers, matching browser/workspace ownership, active status, current seed version, valid file, and valid derived path. The router denies workspace models without its request-scoped alias.

`DemoWorkspaceBackend` never authenticates credentials. It can load only a user ID from the active workspace alias. `DemoAdminSite.has_permission()` additionally requires active staff status. The admin registry is an explicit allowlist, and the synthetic `demo-admin` cannot be deleted or demoted. No control model has a relation to a real site user or main-site model.

The cleanup command is the only scheduled background operation. There is no Celery, Redis, or in-process worker state.
