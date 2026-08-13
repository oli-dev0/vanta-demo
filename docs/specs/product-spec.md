# Vanta Admin Live Demo Product Spec

## Summary

The Vanta Admin live demo is a public, interactive demonstration of the Vanta Django admin theme at `demo.vanta-admin.org`. Visitors can enter an admin panel, browse realistic fictional data, and create, edit, filter, and delete records as they would in a real Django admin installation.

Every visitor receives a private, temporary demo workspace. Changes made by one visitor must never be visible to another visitor. The demo should make this boundary clear while still feeling like a useful admin installation rather than a static screenshot or toy mockup.

The demo consumes the released Vanta Admin package. It is a separate product around the theme and is not part of the reusable Vanta Admin package.

## Product Goal

Let prospective Vanta Admin users experience the theme’s everyday admin workflow with enough realistic data and editable screens to judge its layout, density, navigation, forms, filters, messages, history, preferences, and responsive behavior.

The demo should build trust through three promises:

- It behaves like a real admin panel within the available demo scope.
- A visitor’s changes are private to their temporary workspace.
- Demo content is disposable and remains within the visitor’s private workspace.

## Users and Permissions

- Any visitor can view the public demo introduction and start a demo without creating an account or entering an email address.
- A visitor with an active demo session receives administrator-like access to the seeded demo content inside that session.
- Within their own workspace, a visitor can browse, search, filter, create, edit, and delete the records included in the demo dataset.
- A visitor can use the visible admin preferences and navigation controls, including theme preference, font size, time format, sidebar filtering, sidebar resizing, section expansion, and section reordering where supported by the theme.
- The visitor cannot access the production Vanta website administration, the demo operator’s controls, another visitor’s workspace, or any real customer data.
- A copied or bookmarked admin URL must not grant access to the original visitor’s workspace. It should open the visitor’s own demo or return them to the demo entry point.
- “Demo Admin” is a synthetic identity used to make the panel understandable. It is not a real user account and does not provide access outside the demo.
- Demo operators can maintain the seed content and remove expired workspaces. These controls are not visible to demo visitors.

## Privacy and Data Notes

- The demo should not require a name, email address, password, account, newsletter subscription, payment, upload, or contact form.
- The service needs only an essential browser/session identifier to keep a visitor in the same temporary workspace while they use the demo.
- Limited technical request information, such as an IP address, may be used temporarily for abuse prevention, capacity protection, and rate limiting. It must not be displayed to other visitors or used for marketing.
- Demo workspaces are private, temporary, and disposable. A visitor’s records, edits, deletions, and admin history must not appear in another visitor’s workspace, public page, search result, feed, log-in screen, or social preview.
- A visitor should be told not to enter real personal, confidential, production, or customer data. Seed data must be fictional and must not resemble real customer records.
- Workspaces are removed when the visitor resets the demo or when the workspace expires. No user-facing export is needed because the workspace is intentionally disposable.
- No third-party analytics, advertising pixels, social embeds, email provider, payment provider, or external data service is part of the first version.
- Essential session cookies do not need a marketing consent flow. If non-essential analytics or tracking is added later, the privacy notice, cookie behavior, and consent experience must be revisited before launch.
- The public site should provide a concise privacy notice explaining the temporary workspace, essential session cookie, abuse-prevention data, and retention behavior.

## Scope

### Included now

- A public demo introduction at `demo.vanta-admin.org` with a clear “Try the demo” action.
- A one-step start flow with no account creation or login requirement.
- A seeded, fictional admin dataset that provides meaningful list, detail, edit, delete, relationship, inline, search, filter, and history scenarios.
- A dashboard with realistic sample activity and enough records to make the admin layout visible immediately.
- The Vanta admin shell, including the sidebar, dashboard, model navigation, paginated changelists with a result summary and page jump, dynamically added inline rows, forms, messages, breadcrumbs, object history, account menu, and responsive mobile navigation.
- Safe use of normal admin interactions inside the private workspace, including saving changes, deleting demo records, filtering lists, using supported bulk actions, and reviewing local activity history.
- Demonstration of Vanta-specific preferences and navigation behavior in light and dark mode.
- A persistent “Demo mode” notice explaining that changes are private and temporary.
- A “Start fresh demo” action that discards the current workspace and restores the clean seed experience.
- Clear expired-session, capacity, rate-limit, disabled-cookie, and unexpected-failure states.
- English-first, locale-ready public and admin copy.
- Keyboard-friendly, responsive, and light/dark-mode behavior.

### Recommended first-version dataset

The demo should contain a small fictional editorial workspace, such as articles, categories, tags, and a few related records. It should also contain fictional users and groups so visitors can see familiar access-management screens without being given access to real accounts.

The dataset should be large enough to demonstrate pagination, search, filters, empty results, relationships, inline editing, many-to-many selection, deletion confirmation, success messages, and activity history. It should remain small enough that a visitor can understand it without a tutorial.

## User Flows

### Start a demo

1. A visitor opens the public demo URL.
2. They see what the demo is, which theme release it represents, and that changes are private and temporary.
3. They select “Try the demo”.
4. The page shows a short starting state while the visitor’s private workspace is prepared.
5. The visitor arrives at the demo dashboard with seeded data and a visible “Demo mode” notice.
6. If a workspace cannot be started, the visitor sees a plain explanation and a retry action. Their browser should not be left on a confusing blank admin page.

### Continue an active demo

1. A visitor returns to the demo in the same browser while their workspace is still active.
2. The demo restores that visitor’s own changes and current preferences where possible.
3. The visitor can continue working without starting a second workspace.

### Browse and edit demo data

1. The visitor opens a model from the sidebar or dashboard.
2. They browse a list of fictional records and use search, filters, pagination, or supported bulk actions.
3. They open a record and edit its available fields.
4. They select “Save” and see a success message while remaining in a sensible place in the workflow.
5. The changed record and the corresponding local activity appear in the visitor’s workspace.
6. If validation fails, the form remains open, the entered values are preserved where safe, and each problem is explained next to the relevant field.

### Delete a demo record

1. The visitor chooses a supported delete action for a demo record.
2. A focused confirmation screen or dialog explains that the deletion affects only this private demo workspace.
3. The visitor can cancel and return without losing their place.
4. On confirmation, the record is removed from that workspace and a clear success message appears.
5. The deletion is reflected in the visitor’s local activity history where the admin experience normally exposes history.

### Reset the workspace

1. The visitor selects “Start fresh demo” from the demo notice or account menu.
2. A confirmation dialog explains that all edits, created records, deletions, preferences, and local activity in the current workspace will be discarded.
3. The visitor can cancel and continue working.
4. On confirmation, the visitor receives a clean seeded workspace and a short success message.
5. The reset action does not affect any other visitor.

### Session expires

1. A visitor returns after their temporary workspace has expired or has been removed to protect capacity.
2. The demo explains that the previous workspace is no longer available and that its changes were disposable.
3. The visitor selects “Start a new demo”.
4. A fresh seeded workspace opens.

### Demo capacity or rate limit is reached

1. A visitor tries to start or reset a demo while the service has temporarily reached its protection limit.
2. The visitor sees a clear message that the demo is temporarily unavailable or that they should wait before trying again.
3. The page provides a retry action and, where useful, a link back to the public Vanta Admin website.
4. The message must not reveal internal capacity details or imply that the visitor’s data was shared.

### Use a copied demo link

1. A visitor copies an admin URL or opens one in a different browser.
2. The copied URL does not reveal or load the original workspace.
3. The visitor is taken to their own demo start state or the public demo entry point.
4. The original visitor’s records remain available only in the original active session.

## Screens and Page Behavior

### Public demo introduction

The public page should explain the interactive demo before asking the visitor to start. It should include:

- A Vanta Admin identity and a short description of the theme.
- A primary “Try the demo” action.
- A displayed label for the installed Vanta Admin release.
- A short explanation that the panel uses fictional data and that changes are private to the visitor’s temporary workspace.
- A compact overview of what visitors can try: dashboard, navigation, lists, forms, filters, history, preferences, and mobile behavior.
- A secondary link to the main Vanta Admin website or documentation.
- A privacy link, use the existing vanta_site legal page.

The first viewport should make the primary action obvious without requiring a long marketing page. The page may include a small visual preview, but the interactive demo action must remain the main call to action.

On mobile, the description, privacy note, and primary action should remain visible without requiring a complex navigation menu. The page should not make the visitor scroll through marketing content before they can start.

The start button shows a busy state after activation and prevents accidental duplicate starts. A start failure returns the visitor to a usable public state with a clear retry action.

### Demo admin dashboard

The dashboard is the first screen inside the workspace. It should show the Vanta admin shell with:

- A visible “Demo mode” notice near the top of the admin experience.
- A welcome message identifying the visitor as “Demo Admin”.
- Sample recent activity generated from the seeded dataset.
- Links or cards that lead into the available demo models.
- Enough populated content to demonstrate the theme’s spacing, hierarchy, cards, messages, and activity treatment.

The dashboard should remain useful after the visitor deletes or changes records. If the visitor removes all records from a section, that section shows a clear empty state instead of broken layout or fake activity.

### Admin shell and navigation

The admin shell should demonstrate the installed Vanta Admin experience rather than a simplified mock panel. It should include the visible sidebar, model navigation, search/filter behavior, breadcrumbs, account menu, messages, and responsive mobile navigation that the release provides.

Visitors may collapse, expand, filter, resize, or reorder navigation sections where those interactions are available. Their navigation choices are local to their browser and do not change the experience for anyone else.

The shell should keep the “Demo mode” notice available on every important admin screen. It should not be possible to mistake the sandbox for a production administration area.

### Model list and detail screens

Model list screens should provide enough records to demonstrate:

- Search and clear-search behavior.
- Changelist filters and active-filter feedback.
- Pagination.
- Row selection and supported bulk actions.
- Clear add and edit actions.
- Delete actions with confirmation.
- Useful empty and filtered-empty states.

Detail screens should show realistic forms with visible labels, readable help text, inline relationships where relevant, many-to-many selection where relevant, clear save actions, and understandable validation. Saving, changing, and deleting records should update only the current visitor’s workspace.

On mobile, list data should stack or adapt into readable blocks. No essential action or value should require horizontal scrolling.

### Activity and object history

The demo should include local activity generated by the visitor’s actions and by the seed content where the theme normally displays recent activity or object history.

History should make clear that it belongs to the current temporary workspace. Deleted demo records may remain represented in history as historical actions, but no other visitor’s history should be visible.

### Account menu and preferences

The account menu should identify the synthetic “Demo Admin” user and expose preferences that are safe to demonstrate, such as:

- Light or dark mode.
- Font size.
- 12-hour or 24-hour time display where supported.
- A way to start a fresh demo.
- A way to return to the public demo introduction.

The menu must not suggest that the visitor can change a real password, configure a real two-factor device, send email, or manage a real account. If a theme control has no meaningful demo behavior, it should be disabled with an explanation or omitted.

### Reset confirmation

“Start fresh demo” should use a focused confirmation dialog or page because it discards the visitor’s work. The confirmation must describe the consequence in plain language, provide “Cancel” and “Start fresh demo” actions, and return focus predictably after cancellation.

On small screens, the confirmation may use a full-width dialog or dedicated confirmation view, but it must remain easy to read and operate without accidental confirmation.

### Expired or unavailable demo

The expired state should explain what happened without exposing internal details. It should offer “Start a new demo” as the primary action and “Back to demo overview” as a secondary action.

The unavailable state should distinguish, where possible, between a temporary capacity limit, a request-too-soon protection limit, and a general failure. Each state should provide a next action a visitor can understand.

## Content and Copy

### Public introduction

- Eyebrow: “Live demo”
- Heading: “Try Vanta Admin in a real Django admin workflow.”
- Body: “Explore the Vanta interface with fictional data. Create, edit, filter, and delete records inside a private temporary workspace.”
- Version label: the installed Vanta Admin release.
- Primary action: “Try the demo”
- Secondary action: “Learn about Vanta Admin”
- Privacy note: “Your demo changes are private to this session and will be cleared when the workspace expires or you start fresh.”
- Data warning: “Use fictional demo data. Do not enter personal, confidential, or production information.”

### Demo notice

- Label: “Demo mode”
- Text: “You are in a private workspace. Changes here are not shared with others.”
- Reset action: “Start fresh demo”
- Exit action: “Back to demo overview”

### Dashboard and navigation

- Dashboard heading: “Demo Admin”
- Supporting text: “Explore the Vanta Admin interface with fictional project data.”
- Activity heading: “Recent activity”
- Navigation filter label: “Filter navigation”
- Clear navigation filter: “Clear search”
- Empty navigation result: “No matching admin areas.”

### Forms and messages

- Save success: “Your changes were saved in this demo workspace.”
- Create success: “The record was added to this demo workspace.”
- Delete success: “The record was deleted from this demo workspace.”
- Empty list: “There are no records here yet.”
- Filtered empty list: “No records match these filters.”
- Reset confirmation heading: “Start a fresh demo?”
- Reset confirmation text: “This will discard everything you changed in this workspace, including records, deletions, preferences, and activity.”
- Cancel action: “Keep working”
- Confirmation action: “Start fresh demo”
- Data-safety helper: “Use fictional demo data. Do not enter real personal or production data.”
- Invalid form error: “Review the highlighted fields and try again.”

### Session and capacity states

- Starting state: “Preparing your private demo…”
- Expired heading: “Your demo workspace has expired.”
- Expired text: “Demo workspaces are temporary, so the previous changes are no longer available.”
- Expired action: “Start a new demo”
- Capacity heading: “The demo is busy right now.”
- Capacity text: “Please wait a moment and try again.”
- Rate-limit text: “Please wait before starting another demo.”
- General failure text: “We could not open the demo right now. Please try again.”
- Retry action: “Try again”

Copy should not claim that the demo is production-ready, guarantee permanent storage, or imply that changes are shared with a team. It should not include fake customer names, testimonials, usage figures, or real personal details.

## Forms and Inputs

- Starting the demo requires no form fields.
- The admin forms should use the fields needed to demonstrate the selected fictional models, while keeping the dataset focused and understandable.
- Every writable field must have a visible label and, where needed, short helper text explaining the kind of fictional data to use.
- Search and filter fields are temporary controls and should not be presented as saved content. They must still be escaped and safely handled as ordinary user input.
- Email-like fields should use fictional example values. The demo must not send email or imply that an email address was contacted.
- URL-like fields should not trigger external requests, webhooks, previews, or other side effects. They are demonstration values only.
- File upload fields and integrations that would send data outside the workspace should not appear in the first-version dataset.
- Delete and reset actions require explicit confirmation. Ordinary saves do not require a second confirmation.
- After a successful action, the visitor remains in a predictable place and receives a readable success message.

## States and Edge Cases

- **First visit:** The visitor sees the public introduction and must consciously start the demo.
- **Starting:** The primary action shows progress and cannot be activated repeatedly.
- **Active workspace:** The visitor sees the demo notice and can work with seeded or self-created records.
- **No records:** A deleted or never-populated list shows a useful empty state rather than a blank panel.
- **No filter matches:** The list explains that there are no matches and offers a way to clear filters.
- **Invalid field value:** The form stays open, highlights the problem, and preserves safe input.
- **Duplicate record:** The form explains the conflict in plain language and preserves the visitor’s corrections where possible.
- **Delete cancellation:** The visitor returns to the prior screen without losing their place or accidentally deleting the record.
- **Reset cancellation:** The current workspace remains unchanged.
- **Workspace reset:** Only the current visitor’s workspace is discarded and a clean seed state is shown.
- **Session expiry:** The old workspace is unavailable and a fresh demo can be started.
- **Copied or stale admin URL:** No prior workspace is disclosed; the visitor is routed to their own start state or the public entry point.
- **Browser cookies disabled or unavailable:** The demo explains that it needs an essential session to keep the workspace private and offers a way back to the overview.
- **Capacity limit:** The visitor sees a temporary, actionable unavailable state without internal infrastructure details.
- **Rate limit:** Repeated start/reset attempts receive a clear wait message and do not create additional workspaces.
- **Unexpected request failure:** The visitor sees a recoverable error, and the page does not show another visitor’s data.
- **Preferences:** Theme, font-size, time-format, sidebar, and other browser-local preferences affect only the current visitor’s browser.
- **Multiple tabs:** Tabs belonging to the same active session may reflect the same visitor’s workspace. A different browser or session must not see it.
- **Back/forward navigation:** Browser navigation must not expose a discarded workspace or bypass the demo boundary.
- **Long text:** Saved content remains readable and does not break the layout on desktop or mobile.

## Navigation and Links

- The public demo URL is the primary entry point.
- “Try the demo” opens the visitor’s private admin workspace.
- The Vanta Admin logo or “Back to demo overview” returns to the public demo introduction without exposing workspace data there.
- The demo notice and account menu both provide “Start fresh demo”.
- Normal admin breadcrumbs, sidebar links, search, filters, pagination, and object links stay within the current workspace.
- The account menu’s exit action returns to the public overview and does not imply that a real account was logged out.
- Links to Vanta Admin documentation, source code, releases, and the main website open their public destinations when available.
- A public link must never contain or reveal enough information to open another visitor’s workspace.
- Reset, expiry, and unavailable states provide an obvious route back to the public overview.

## SEO and Sharing

The public demo introduction should be indexable and shareable because it is a public product entry point.

- Suggested title direction: “Vanta Admin Live Demo | Django Admin Theme”.
- Suggested description direction: “Try Vanta Admin in an interactive Django admin demo with fictional data and a private temporary workspace.”
- The canonical public URL is `https://demo.vanta-admin.org/`.
- Social previews should represent the Vanta Admin demo and should not contain user-created demo content.
- The admin workspace, all workspace-specific screens, reset/expiry states, and any URL containing session context should not be indexable or included in public sharing previews.
- Workspace pages do not need RSS.
- The public introduction may link to the Vanta Admin release or documentation pages, but it should not expose private workspace URLs.

## Locale and Language Notes

- English is the initial source language for the public page, demo notice, admin additions, validation messages, and session states.
- All product copy, labels, and error messages should be ready for translation.
- A future language switcher should be available from the public page and remain usable inside the demo where relevant.
- Future translated public pages should use clear language-specific URLs and preserve the same demo-start behavior.
- If a translation is unavailable, English is the fallback.
- Date, time, and number presentation should follow the selected language and the existing admin preference behavior.
- Language selection must use the URL, visitor choice, or browser language. IP address and geolocation must not select the language.

## Accessibility and UX Notes

- All links, buttons, fields, filters, table/list actions, dialogs, and navigation controls need visible names and clear purpose.
- Every form field must have a visible associated label. Placeholder text must not be the only label.
- Keyboard users must be able to start, navigate, search, filter, edit, save, cancel, delete, reset, and exit the demo.
- Focus must remain visible in light and dark mode and must move predictably into and out of reset/delete dialogs.
- Confirmation dialogs must expose their heading and consequence to assistive technology and support Escape-to-cancel where appropriate.
- Save errors and session states should be announced or placed where a screen-reader user can find them without scanning the entire page.
- Color must not be the only way to communicate status, active filters, success, or errors.
- Admin lists and forms must remain usable at narrow widths without requiring horizontal scrolling for essential content or actions.
- Touch targets should be comfortable on mobile, including sidebar controls, filter toggles, pagination, save actions, and confirmation buttons.
- Expansion, sidebar movement, messages, and dialogs should respect reduced-motion preferences.
- The public page and admin workspace should support both light and dark mode. The default should follow the visitor’s system preference, with an explicit control available where the theme provides one.
- The page should use readable contrast, restrained density, and clear hierarchy so the demo showcases Vanta’s visual design without reducing usability.

## Acceptance Criteria

- A visitor can open `demo.vanta-admin.org` and understand that it is an interactive Vanta Admin demo.
- A visitor can start the demo without creating an account or entering an email address.
- The demo identifies the installed Vanta Admin release.
- The visitor enters an admin panel with seeded fictional data rather than an empty or static screenshot-only experience.
- The visitor can browse the dashboard, sidebar, model lists, detail pages, forms, filters, search, pagination, messages, and available history screens.
- The visitor can create and edit supported demo records.
- The visitor can delete supported demo records after an explicit confirmation.
- The visitor can use supported relationships, inline forms, many-to-many controls, and bulk actions where the seeded dataset exposes them.
- A valid save changes only the current visitor’s temporary workspace and shows a clear success message.
- A visitor’s changes are not visible in a separate browser session, a different visitor’s demo, a public page, a shared link, or another person’s activity history.
- A visitor can use “Start fresh demo” to discard their current changes and receive the clean seeded experience.
- Resetting one workspace does not reset or alter another workspace.
- A visitor sees a persistent “Demo mode” notice that explains privacy and temporary retention.
- A copied or stale admin URL cannot reveal the original visitor’s workspace.
- Email-like fields do not send messages, and external URL-like values do not trigger external side effects.
- The demo provides clear empty, filtered-empty, validation-error, expired, capacity, rate-limit, disabled-cookie, retry, and general-failure states.
- Expired workspaces can be replaced with a new demo without exposing the old workspace.
- The public introduction is indexable at the canonical demo URL, while workspace pages are not indexable.
- Social previews never include visitor-created demo content.
- The experience is usable with keyboard navigation, visible focus, readable errors, touch controls, light mode, dark mode, and narrow mobile layouts.
- Public and demo-specific copy is English-first and ready for translation without using IP geolocation to select a language.

## Out of Scope

- Real user accounts, registration, passwords, or visitor login.
- Real two-factor authentication setup or recovery.
- Access to a production Django admin, real customer data, or the demo operator’s administration.
- Collaboration or shared workspaces between visitors.
- Permanent storage, downloadable backups, record export, or workspace sharing.
- Email sending, newsletter signup, webhooks, payments, external integrations, and third-party data services.
- File uploads or media processing that would add unnecessary storage or external-data risk.
- A complete production CMS or an attempt to reproduce every possible Django admin model.
- Public display, search, RSS, analytics, or social sharing of visitor-created content.
- Native mobile applications.
- A separate Vanta theme feature that owns demo-specific data or behavior.

## Mobile Handoff Notes

There is no native mobile app in the current project scope. If a future mobile experience is created, it should preserve these product rules:

- The visitor can start without an account and receives a private temporary workspace.
- Workspace isolation, expiry, reset, and no-cross-visitor-visibility guarantees remain identical.
- The mobile experience should keep the same fictional dataset, permissions, success/error states, and “Demo mode” explanation.
- Dense desktop tables should become stacked cards or focused list/detail flows on small screens.
- Sidebar navigation should become a simple mobile navigation surface; drag-reordering and wide relationship selectors may need a different interaction.
- Reset and delete confirmations must remain explicit and easy to cancel on touch devices.
- Theme, font-size, time-format, and other preferences should be mapped to platform-appropriate controls without changing their meaning.
- The mobile experience should not assume that a shared demo URL can carry a workspace between devices.
- A later mobile plan must preserve the prohibition on real personal data and external side effects.

## Assumptions

- The first version is anonymous and one-click; a synthetic “Demo Admin” identity is clearer and lower-friction than asking visitors to log in.
- A visitor’s workspace is tied to an active browser session and can persist across normal navigation and multiple tabs in that session.
- Temporary workspaces expire after a bounded period of inactivity. The exact retention period and capacity limits belong to the later operational design, but the user experience must explain expiry clearly.
- Starting and resetting are protected against excessive repetition, and the service may temporarily refuse new workspaces when safe capacity is reached.
- The seed dataset is fictional, intentionally small, and curated to exercise the theme’s representative admin interactions rather than every Django feature.
- The demo consumes the released Vanta Admin package; later theme releases update the package, seed, checks, tests, and visible release label without changing this product specification.
- The demo allows realistic destructive actions inside the sandbox because isolation and reset are more valuable for evaluation than a read-only tour.
- Essential session handling is required to maintain the private-workspace guarantee. No non-essential tracking is assumed.
- The public page is indexable; workspace-specific pages are private and not indexable.
- The demo is a standalone consuming application around the Vanta theme and does not expand the reusable theme package’s product scope.

## Open Questions

None.
