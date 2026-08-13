# Locale and language behavior

## Current behavior

The demo launches English-only with `LANGUAGE_CODE='en'`, `LANGUAGES=[('en', 'English')]`, `USE_I18N=True`, `LocaleMiddleware`, and the shared `common/locale` path. There is no language-prefixed demo URL and no language switcher on the overview. Browser `Accept-Language` cannot select a language outside the configured allowlist; English is the only active fallback.

All feature-owned static copy in Python and templates uses Django gettext primitives (`gettext_lazy`, `gettext`, `{% translate %}`). The feature’s strings live in `apps/vanta_demo/`; no non-English catalog has been added yet. The public canonical, sitemap, Open Graph, and Twitter URLs are the single English demo URL.

## Data translations

Seeded blog articles and projects have English translation rows in `demo_content` and `demo_projects` so the admin can demonstrate translation-related inlines. Those rows are fictional workspace data, not a translation of the public Vanta site. No translated demo slugs or locale-specific SEO pages exist.

## Request behavior

Not applicable: there is no DRF API, so there are no `Accept-Language` or `Content-Language` response headers.

## Deferred work and gaps

Adding a second language would require a deliberate locale change: add the supported code, feature-owned catalog, language-selection/URL strategy, translated public metadata, sitemap/canonical behavior, and tests. Use the `translate-locale` workflow for that work. Do not infer locale from IP address or add translations directly to the seed without deciding whether they are demo content or UI copy.
