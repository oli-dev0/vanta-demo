# Vanta Admin interactive demo

## Purpose and location

The Vanta Admin demo lets a visitor try the Vanta Django admin theme with fictional, editable data. The seed covers users and groups plus representative blog, project, newsletter, service-status, and contact workflows. It is a standalone consuming product around the released theme package, owned by this repository.

The public entry point is `https://demo.vanta-admin.org/`. The implementation is a dedicated Django runtime selected with `DJANGO_SETTINGS_MODULE=config.settings.demo`. This repository owns the demo runtime and its documentation.

## Surfaces

- Public overview: `GET /`
- Dedicated admin: `/admin/`
- Workspace lifecycle: `/start/`, `/reset/`, `/expired/`
- Operational endpoints: `/healthz/`, `/readyz/`
- Public discovery: `/robots.txt`, `/sitemap.xml`
- DRF/API client: not implemented; the browser uses Django views and the normal admin HTML workflow.

## Main flow

1. The visitor opens the overview and receives an essential session cookie plus a short-lived start marker.
2. `POST /start/` validates the session marker, rate limit, and capacity, then copies the immutable seed into a UUID-derived SQLite file.
3. The session points to that workspace and Django signs in the synthetic `Demo Admin` user through the demo-only authentication backend.
4. Admin requests are routed to the current workspace file. Control records and session rows remain in the dedicated PostgreSQL database.
5. The visitor may edit the allowlisted models, continue until idle expiry, or reset to a newly seeded workspace.

## Permissions and privacy

Visitors do not create accounts or supply credentials. Access exists only while the request has a valid browser/session binding, active workspace lease, valid seed version, and valid workspace file. The synthetic administrator has no usable password and is protected from deletion or demotion.

Workspace IDs are not accepted from URLs or forms. A copied admin URL without the matching session cannot load the original workspace. Demo data is fictional and disposable; visitors are warned not to enter personal, confidential, or production information.

## Source documents

- [Product specification](./specs/product-spec.md)
- [Technical specification](./specs/tech-spec.md)
The implementation and passing tests are the current source of truth when the planning documents describe behavior that is not yet implemented or browser-verified.
