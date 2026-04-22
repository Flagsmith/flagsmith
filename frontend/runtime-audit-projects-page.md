# Flagsmith runtime audit — `http://localhost:8080/organisation/3905/projects`

## Environment

- Chrome version: Chromium (via Chrome DevTools MCP)
- Viewport: 1440×900
- Mode(s): Both light and dark
- User agent: Not directly readable; Chromium-based
- Token drift check: **CONDITIONAL PASS** — semantic CSS tokens are scoped correctly to `.dark` on `<body>`, not on `:root`. The standard Phase 0.5 script (reading from `document.documentElement`) reports identical light/dark values because dark overrides live on `body.dark`. Dark values are correct when read from `getComputedStyle(document.body)`. One true drift: `--radius-2xl` = `1rem` (16px) but rules specify 18px. All other sampled tokens pass.

---

## Summary

- Pages audited: 1 (`/organisation/3905/projects`)
- Components inspected: project card tile, "Create project" tile, search input, navigation tabs, avatar span, sort control link, logo link
- States covered: default, hover, focus
- Findings: 0 critical, 7 major, 8 minor
- Overall compliance: medium — the `ProjectLetterAvatar` accessibility fix landed correctly, but focus rings are absent on interactive buttons, the page title uses the wrong heading tag and size, and the descriptor uses the wrong colour token in both modes

---

## Critical findings

None. The avatar `<h2>` → `<span aria-hidden>` change resolves the previously-critical heading impersonation. No remaining critical findings were found at runtime.

---

## Major findings

### MAJOR-1: Page title heading tag and size wrong — `PanelSearch` renders `<h5>` at 18px

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `h5.m-b-0.title` (text: "Projects")
- **State:** default
- **Mode:** both
- **Expected:** `<h1>` (new pages) or `<h2>` (legacy) at `$h2-font-size` = 34px / weight 600, per `composition.md` §2 and `typography.md` tag→role mapping
- **Actual (computed):** `font-size: 18px; font-weight: 700; tag: H5` — this is the card-title level, not the page-title level. Weight 700 is also a violation (rules require 600 for headings).
- **Screenshot:** `audit-screenshots/composition-overlay.png` — red outline shows `<h5>` at 18px as the page title in the top-left of the content area
- **Violation:** The page title "Projects" renders at `<h5>` 18px when composition rules require the page title to be rendered at `<h1>`/`<h2>` 34px; screen readers will announce this as a level-5 heading, misrepresenting the document outline.
- **Suggested fix:** Route to `design-auditor` against `frontend/web/components/shared/PanelSearch.tsx` — `title` prop should render as `<h1>` (preferred) or `<h2>` (legacy) using `$h2-font-size`. The font-weight should be 600 (`$font-weight-semibold`), not 700.

---

### MAJOR-2: Focus ring absent on project card buttons and "Create project" button

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `button.btn-project` and `button.btn-project-create` (text: "test", "Create project")
- **State:** focus
- **Mode:** both
- **Expected:** `box-shadow: 0 0 0 2px var(--color-surface-default), 0 0 0 4px var(--color-border-action)` or minimum 2px outline in `var(--color-border-action)` (#6837fc light / #906af6 dark), per `accessibility.md` focus spec
- **Actual (computed):** `outline: none (0px, style=none); box-shadow: none` — completely absent focus ring in both light and dark modes
- **Screenshot:** `audit-screenshots/phase3-focus-project-card.png` — no visible focus ring on the focused project card
- **Violation:** WCAG 2.4.13 (Focus Appearance) — programmatic focus produces no visible indicator on these interactive buttons.
- **Suggested fix:** Route to `design-auditor` against `frontend/web/styles/project/_buttons.scss` — the `.btn-project` variant needs a `:focus-visible` rule adding `box-shadow: 0 0 0 2px var(--color-surface-default), 0 0 0 4px var(--color-border-action)`. Do not remove the existing `outline: none` without the replacement in place.

---

### MAJOR-3: Descriptor uses `--color-text-default` instead of `--color-text-secondary` in both modes

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `div.fs-small.mb-2.lh-sm` (text: "Projects let you create and manage a set of features...")
- **State:** default
- **Mode:** both (light: `rgb(26, 38, 52)` = white equivalent; dark: `rgb(255, 255, 255)` = white)
- **Expected:** `color: var(--color-text-secondary)` = `#656d7b` light / `#9da4ae` dark, per `composition.md` §1 — "Check descriptors resolve to `--color-text-secondary`"
- **Actual (computed):** Light: `rgb(26, 38, 52)` = `--color-text-default`. Dark: `rgb(255, 255, 255)` = `--color-text-default`. Descriptor renders at the same weight as body text, providing no visual hierarchy between the heading and the description.
- **Screenshot:** `audit-screenshots/phase1-dark-mode.png` — in dark mode the descriptor text is the same white as the heading "Projects"
- **Violation:** Descriptor uses the default body colour instead of the secondary colour; the visual hierarchy between heading and descriptor is lost.
- **Suggested fix:** Route to `design-auditor` against the descriptor element (likely a `<p>` or `<div>` in `PanelSearch.tsx` or `ProjectManageWidget.tsx`) — change the colour class from a default text class to `text-secondary` or apply `color: var(--color-text-secondary)` directly.

---

### MAJOR-4: Heading→descriptor gap 17px (spec: 4–6px); descriptor→content gap −8px (spec: 12–16px)

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** heading `<h5>` → `div.fs-small.mb-2.lh-sm` → `div.row.mt-n2`
- **State:** default
- **Mode:** both
- **Expected:** Heading→descriptor gap 4–6px (they are one visual unit); descriptor→content gap 12–16px, per `composition.md` §1
- **Actual (computed):** Heading bottom: 141px; Descriptor top: 158px → gap = **17px** (3× too large). Descriptor bottom: 178px; Content row top: 170px → gap = **−8px** (content overlaps descriptor by 8px due to `mt-n2` Bootstrap class).
- **Screenshot:** `audit-screenshots/composition-overlay.png` — red=heading, blue=descriptor, green=content; the green row's top border sits above the blue descriptor's bottom border.
- **Violation:** The negative margin on the content row causes it to visually overlap the descriptor; simultaneously the heading is too far from the descriptor, breaking the "one unit" grouping required by the composition pattern.
- **Suggested fix:** Route to `design-auditor` against `PanelSearch.tsx` / `ProjectManageWidget.tsx` — remove `mt-n2` from the content row and set the heading-block margin to `mb-1` (4px gap between heading and descriptor), with `mb-3` (16px) gap between descriptor and content grid.

---

### MAJOR-5: Logo home link has no accessible name — missing `aria-label` and `alt` on `<img>`

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `a[data-test="home-link"]` containing `<img src="/static/images/nav-logo.png">` (no text content)
- **State:** default
- **Mode:** both
- **Expected:** Icon-only links must have `aria-label` per `accessibility.md` and WCAG 4.1.2; the `<img>` must have an `alt` attribute
- **Actual (computed):** `aria-label: null`, `img alt: null`, accessible text computed as empty string. Screen readers will announce the `src` URL as the link text.
- **Screenshot:** `audit-screenshots/phase0-initial.png` — the Flagsmith logo in the top-left corner is the affected element
- **Violation:** The logo link provides no accessible name; screen readers will announce the image filename as the link destination, violating WCAG 4.1.2 Name, Role, Value.
- **Suggested fix:** Add `aria-label="Flagsmith home"` to the `<a>` tag OR add `alt="Flagsmith"` to the `<img>`. Route to `design-auditor` against the top-navigation component.

---

### MAJOR-6: GitHub icon invisible in dark mode — SVG `fill="#000000"` hard-coded black

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** GitHub icon SVG (16×16) in the top navigation, `path[fill="#000000"]`
- **State:** default
- **Mode:** dark only
- **Expected:** The GitHub icon should use `fill="currentColor"` or `fill="var(--color-icon-secondary)"` so it flips from dark-on-light to light-on-dark
- **Actual (computed):** `fill: rgb(0, 0, 0)` in dark mode — black icon on `rgb(16, 22, 40)` dark background. Non-text contrast ratio ≈ 1.13:1 (fails 3:1 minimum).
- **Screenshot:** `audit-screenshots/dark-github-icon.png` — the GitHub mark to the left of "6.4k" is invisible; only the text label remains visible.
- **Violation:** Hard-coded `#000000` fill makes the GitHub icon invisible in dark mode; fails WCAG 1.4.11 Non-text Contrast (3:1 required).
- **Suggested fix:** Change the SVG path `fill="#000000"` to `fill="currentColor"` so it inherits the parent's colour, which will be white in dark mode. Route to `design-auditor` against the GitHub icon SVG component.

---

### MAJOR-7: Project card uses wrong surface elevation in dark mode (`--color-surface-emphasis` instead of `--color-surface-subtle`)

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `button.btn-project.btn-primary` (the project card tile for "test")
- **State:** default
- **Mode:** dark only
- **Expected:** Card background = `var(--color-surface-subtle)` = `#15192b` (`$slate-900`) in dark mode, per `color.md` surface stack ("Cards, tables, KPI tiles — one step up from page")
- **Actual (computed):** `background-color: rgb(32, 40, 57)` = `#202839` = `--color-surface-emphasis` (`$slate-800`). This is two steps above the page background, not one.
- **Screenshot:** `audit-screenshots/phase1-dark-mode.png` — the "test" project card has a noticeably elevated surface
- **Violation:** The project card uses the "strongest neutral fill" elevation instead of the card elevation, creating too strong a contrast step and potentially breaking the visual hierarchy if deeper elements also use `surface-emphasis`.
- **Suggested fix:** Route to `design-auditor` against `frontend/web/styles/project/_buttons.scss` — the `.btn-project` background rule in dark mode should resolve to `var(--color-surface-subtle)` not `var(--color-surface-emphasis)`. Check if a `.dark` selector override is causing the escalation.

---

## Minor findings

### MINOR-1: Focus ring on search input is 1px border change only (spec: 2px minimum perimeter)

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `input.input.input-sm` (Search)
- **State:** focus
- **Mode:** light (in dark mode the border doesn't change at all on computed styles, though visual may differ)
- **Expected:** 2px minimum focus perimeter in `var(--color-border-action)`, per `accessibility.md` focus spec
- **Actual (computed):** On focus: `border-color: rgb(104, 55, 252)` (correct colour) but `border-width: 1px` only; `outline: none; box-shadow: none`. The ring is only 1px thick.
- **Violation:** Focus indicator thickness is 1px, below the 2px minimum required by WCAG 2.4.13 and the accessibility rules.
- **Suggested fix:** Add `box-shadow: 0 0 0 2px var(--color-surface-default), 0 0 0 4px var(--color-border-action)` on `:focus-visible` for `.input` class, in addition to or instead of the 1px border change.

---

### MINOR-2: All navigation `<a>` links use browser-default focus ring (wrong colour, 1px)

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** All `<a>` elements in the top nav and org tabs (e.g., "Projects", "Users and Permissions", "test dd")
- **State:** focus
- **Mode:** both
- **Expected:** 2px `var(--color-border-action)` outline (purple-600 / purple-400)
- **Actual (computed):** `outline: rgb(0, 95, 204) auto 1px` — browser default blue, 1px thickness. Wrong colour, wrong weight.
- **Violation:** Navigation links show the browser's default focus ring instead of the design system's purple `--color-border-action` ring.
- **Suggested fix:** Apply the standard focus-visible style globally in `_base.scss` or `_focus.scss`: `a:focus-visible { outline: none; box-shadow: 0 0 0 2px var(--color-surface-default), 0 0 0 4px var(--color-border-action); }`.

---

### MINOR-3: Sort / "Name" control uses inline `style="color: rgb(101, 109, 123)"` — raw value bypassing token

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `a.flex-row` (the "Name" sort control in the panel heading)
- **State:** default
- **Mode:** both (dark-mode regression — see mode-specific findings)
- **Expected:** `color: var(--color-icon-secondary)` or no inline style, letting the token cascade
- **Actual (computed):** `style="color: rgb(101, 109, 123);"` — hard-coded RGB, anti-pattern #3 (raw hex equivalent in component code)
- **Violation:** Inline colour bypasses the token system and produces a dark-mode regression (see DARK-1 below).
- **Suggested fix:** Route to `design-auditor` against `PanelSearch.tsx` — remove the inline `style` colour and use a CSS class that applies `var(--color-icon-secondary)`.

---

### MINOR-4: `transition: all` on `.nav-sub-link` and `.btn-project-letter`; raw durations throughout

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `a.nav-sub-link`, `span.btn-project-letter`; `.btn-project` buttons use `0.15s ease-in-out`; search input uses `0.2s`
- **State:** default
- **Mode:** both
- **Expected:** `transition: background-color var(--duration-fast) var(--easing-standard)` (or specific properties). `transition: all` is anti-pattern #49; raw durations (#44) and raw easings (#45) are anti-patterns.
- **Actual (computed):**
  - `.btn-project`: `color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out`
  - `input.input-sm`: `0.2s` (bare duration, no property, no easing)
  - `.nav-sub-link`: `transition: all`
  - `.btn-project-letter`: `transition: all`
- **Violation:** Multiple elements use raw duration values and `transition: all`, violating `motion.md` and `anti-patterns.md`.
- **Suggested fix:** Route to `design-auditor` / `token-fixer` against `_buttons.scss` and `_nav.scss` — replace `0.15s ease-in-out` with `var(--duration-fast) var(--easing-standard)`, remove `transition: all`, and name specific properties.

---

### MINOR-5: `<div>` used for descriptor (should be `<p>`)

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `div.fs-small.mb-2.lh-sm` (text: "Projects let you create and manage...")
- **State:** default
- **Mode:** both
- **Expected:** The descriptor slot should be a `<p>` element per `composition.md` §1 and the HTML-tag-to-token mapping (§6)
- **Actual (computed):** `tag: DIV` — a `<div>` is used for a paragraph of descriptive copy. Screen readers treat `<p>` differently from `<div>` (paragraph pause).
- **Violation:** Semantic HTML violation; a text paragraph is expressed as a `<div>`.
- **Suggested fix:** Route to `design-auditor` against `PanelSearch.tsx` — change the descriptor wrapper from `<div>` to `<p>`.

---

### MINOR-6: Heading→descriptor size ratio 1.29 (below 1.3× comfort floor)

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `<h5>` 18px / descriptor `div` 14px — ratio 1.286
- **State:** default
- **Mode:** both
- **Expected:** Heading must out-rank descriptor by ≥1.3×, per `composition.md` §1
- **Actual (computed):** 18 / 14 = 1.286 — 0.014 below the floor
- **Violation:** Ratio is marginally below the 1.3× comfort floor. Confidence: `medium` (proximity to the threshold makes this judgment-dependent).
- **Suggested fix:** This finding resolves automatically if MAJOR-1 is fixed (moving the heading to `<h2>` at 34px would give a 34/14 = 2.43 ratio ✓).

---

### MINOR-7: Two SVG paths in nav icons still use hard-coded `fill="#9DA4AE"` and one uses `fill="#656d7b"`

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** Two 20×20 icon SVGs (navigation icons); one 24×24 icon SVG (sort icon)
- **State:** default
- **Mode:** both (numerically match token in both modes, but bypasses token system)
- **Expected:** `fill="var(--color-icon-secondary)"` as implemented on the "Create project" `+` icon
- **Actual (computed):** `fill="#9DA4AE"` and `fill="#656d7b"` — raw hex literals. These happen to match `--color-icon-secondary` in both modes today, but will break if the token value changes.
- **Violation:** Bypasses the token system; anti-pattern #3 (raw hex in component code).
- **Suggested fix:** Route to `design-auditor` to identify which nav/sort icon components contain these SVG paths and update to `fill="var(--color-icon-secondary)"` or `fill="currentColor"`. The `+` icon fix in `ProjectManageWidget` is the correct pattern to follow.

---

### MINOR-8: `--radius-2xl` token is 16px (1rem) but rules specify 18px

- **Page:** `http://localhost:8080/organisation/3905/projects`
- **Element:** `:root` CSS custom property (no component using it visible on this page)
- **State:** default
- **Mode:** both
- **Expected:** `--radius-2xl: 18px`, per `design-tokens.md` radius table ("large featured surfaces / modals")
- **Actual (computed):** `--radius-2xl: 1rem` = 16px at the root font-size of 16px
- **Violation:** Token drift — the radius token for modal/large-surface rounding is 2px short of specification. Likely harmless at this page but would produce incorrect modal rounding.
- **Suggested fix:** Update `frontend/common/theme/tokens.json` to set `radius-2xl: 18px` (not `1rem`) and regenerate `_tokens.scss`. Alternatively, verify whether the SCSS variable `$modal-border-radius: 18px` is being used directly in modals (bypassing the CSS custom property), in which case this is a token-vs-SCSS-var split that should be reconciled.

---

## Mode-specific findings

### DARK-1: Sort / "Name" control hard-coded colour is wrong in dark mode

- **Element:** `a.flex-row` (sort control), `style="color: rgb(101, 109, 123)"`
- **Mode:** dark only
- **Issue:** `rgb(101, 109, 123)` = `#656d7b` = light-mode `--color-icon-secondary`. In dark mode, `--color-icon-secondary` = `#9da4ae`. The inline hard-coded value doesn't flip, so the sort icon and "Name" label render with a slightly-too-dark grey against the dark background.
- **Contrast:** `rgb(101, 109, 123)` on `rgb(16, 22, 40)` ≈ 3.9:1 — passes 3:1 non-text floor but only just. Confidence: high.

### DARK-2: "Create project" card border uses hard-coded rgba that doesn't flip in dark mode

- **Element:** `button.btn-project-create`, `border: 1px dashed rgba(101, 109, 123, 0.24)`
- **Mode:** dark only
- **Issue:** `rgba(101, 109, 123, 0.24)` is the light-mode `--color-border-strong`. In dark mode, `--color-border-strong` should be `white @ 24%`. The hard-coded light-mode alpha doesn't flip, making the dashed border too dim against the dark background.

### DARK-3: Search input does not show focus-border colour change in dark mode

- **Element:** `input.input.input-sm`, focused
- **Mode:** dark only
- **Issue:** In light mode, the search input border changes to `rgb(104, 55, 252)` (purple) on focus. In dark mode, the computed border-color on focus remains `rgba(255, 255, 255, 0.08)` — the default border. While the visual screenshot suggests a border may appear, the computed style shows no colour change. This may indicate the focus change is a Bootstrap behaviour that's overridden in dark mode.

---

## Cross-page inconsistencies

Not applicable — only one page was audited. No cross-page comparison is possible.

---

## Viewport-specific findings

Not applicable — desktop only (1440×900) was in scope. Multi-viewport sweep was out of scope per audit brief.

---

## Accessibility violations

**Focus ring missing/wrong on:**

- `button.btn-project` (all project cards) — no ring at all, both modes (MAJOR-2)
- `button.btn-project-create` — no ring, both modes (MAJOR-2)
- All `<a>` navigation links — browser-default blue 1px ring, not design-system purple 2px (MINOR-2)
- `a[data-test="home-link"]` (logo) — browser-default ring; also no accessible name (MAJOR-5)
- `a.flex-row` (sort "Name" control) — `outline: none` effective (no visible ring in computed styles)

**Target size < 24px (WCAG 2.5.8):**

- `a[href*="github.com"]` "6.4k" link: 19×48px — height 19px below 24px minimum
- `a` "Getting Started" link: 20×127px — height 20px
- `a` "Docs" link: 20×73px — height 20px
- `button.account-dropdown-trigger` "Account": 22×101px — height 22px

All four are in the top navigation bar. The header items are generally undersized for interactive elements.

**Contrast failures:**

- Light mode: All sampled text passes (body 15.32:1, descriptor 15.32:1, though descriptor colour should be secondary not default). No actual contrast failure on text.
- Dark mode: GitHub icon `fill="#000000"` on `rgb(16, 22, 40)` ≈ 1.13:1 — fails 3:1 non-text contrast requirement (MAJOR-6). Sort control `rgb(101, 109, 123)` on `rgb(16, 22, 40)` ≈ 3.9:1 — passes 3:1 non-text floor.

**Missing `aria-label`:**

- `a[data-test="home-link"]` — icon-only link with `<img alt="">` (empty/null alt); no `aria-label` on link. Full violation (MAJOR-5).

**Focus trap in modals:** Not audited — no modal was open during the audit session. Triggering the "Create project" modal was out of scope (would require clicking a CTA that opens a form; the modal state was not reachable without state change).

---

## Verification of static-audit-specified fixes

The user requested runtime confirmation of four items from a previous static audit pass:

### Avatar (`btn-project-letter`) — CONFIRMED RESOLVED

- Tag: `<span>` ✓ (changed from `<h2>`)
- `aria-hidden="true"` ✓ — letter does not appear in accessibility tree as a heading
- Font size: 34px ✓ (`$h2-font-size`)
- Font weight: 600 ✓ (`$font-weight-semibold`)
- Line height: 34px ✓ (matches `line-height: 1` × 34px)
- Dimensions: 60×60px ✓
- Centring: `display: flex; align-items: center; justify-content: center` ✓
- `text-transform: uppercase` ✓ — "t" renders visually as "T"
- Accessible name of containing button: "test" (the project name, excluding the `aria-hidden` letter) ✓
- **Colour contrast**: White letter on `rgb(144, 106, 246)` = 3.76:1. The letter is 34px / weight 600 = large text, so 3:1 threshold applies — **passes** the large-text floor. However, the background colour `#906af6` is the dark-mode `$purple-400` value applied in both modes via `Utils.getProjectColour()` inline style. In light mode, `--color-surface-action` is `#6837fc` (7.1:1 contrast) — if this palette colour were replaced by the token, contrast would be much better. The current 3.76:1 is a pass but a marginal one. Confidence: high that it passes; medium that it's the right choice.

### `PanelSearch` title — STILL A FINDING (MAJOR-1)

- `PanelSearch` renders the `title` prop as `<h5>` at 18px / weight 700.
- This is confirmed at runtime as MAJOR-1 above. The static audit's MAJOR-4 finding is valid.

### Icon fills — PARTIALLY RESOLVED

- The `+` icon in "Create project" correctly uses `fill="var(--color-icon-secondary)"` ✓
- Computed fill: `rgb(101, 109, 123)` = `--color-icon-secondary` in light mode ✓
- **Two nav icons still use `fill="#9DA4AE"`** (hard-coded) — see MINOR-7
- **Sort icon still uses `fill="#656d7b"`** (hard-coded) — see MINOR-7
- The static fix was partial; not all icons were updated.

### Card wrapper `min-width: 190px` — NO OVERFLOW AT 1440px

- At 1440px with the 1200px max-width container and `col-xl-3` (25% of 1200px ≈ 300px), the card renders at 305px width — well above the 190px minimum.
- No overflow. ✓

### Descriptor paragraphs (empty state) — NOT TESTABLE

- Only one project exists ("test") — the empty state does not render. The descriptor paragraphs under `<h5>Create your first project</h5>` were not visible. Cannot confirm.

---

## Scope limits

- Only one page audited (`/organisation/3905/projects`) — no cross-page consistency possible
- Empty state not reachable (one project exists); empty-state descriptor colour check deferred
- "Create project" modal state not tested (avoided clicking CTA to prevent state change)
- Active/pressed, disabled, loading states not audited (out of scope per brief)
- Multi-viewport check not performed (desktop only per brief)
- Phase 6 (cross-page consistency) not possible with one page
- Four 401 console errors present at load — these appear to be Pylon chat widget requests unrelated to the main application

---

## Confidence

**High:**

- Token resolution in light mode (verified via `getComputedStyle` on live elements)
- Focus ring absence on `.btn-project` buttons (directly measured)
- Avatar implementation (tag, size, weight, aria-hidden all verified)
- GitHub icon dark-mode invisibility (computed fill + screenshot)
- Logo link missing accessible name (verified `aria-label: null`, `img alt: null`)
- Target size violations in the nav bar (measured via `getBoundingClientRect`)
- Descriptor colour using `--color-text-default` instead of `--color-text-secondary`
- Dark-mode project card surface elevation using `--color-surface-emphasis` (confirmed via reload)

**Medium:**

- Sort link dark-mode colour regression (computed but could depend on specificity)
- Heading→descriptor gap and descriptor→content gap (measured via `getBoundingClientRect`)
- Heading size ratio 1.29 (measured but proximity to threshold)
- Partially unresolved icon fills (static source needed to confirm which components were and weren't updated)
- `--radius-2xl` drift (token value confirmed but no modal present to see impact)

**Low:**

- Dark mode search input focus ring behaviour (visual screenshot suggests ring appears but computed style contradicts; browser behaviour may differ from computed style during programmatic focus)
- Descriptor quality / copy tone (passed automated proxy checks; [manual review] items not pursued)

---

## Dark-mode verification (follow-up run)

A second focused run proved the dark-mode pass was real, not claimed:

- Light baseline: `bodyBg: rgb(255,255,255)`, `bodyColor: rgb(26,38,52)`
- After `localStorage.setItem('dark_mode','true')` + reload: `bodyBg: rgb(16,22,40)` (`$slate-950`), `bodyColor: rgb(255,255,255)` — a genuine flip
- Avatar in dark: `bg rgb(144,106,246)` (`$purple-400`), text `rgb(255,255,255)` — as expected
- Light restored at session end: `bodyBg: rgb(255,255,255)` ✓

**Token cascade nuance.** Flagsmith applies `.dark` to `<body>`, and the override rule `.dark { --color-surface-default: ...; }` kicks in on `body.dark` and its descendants. Custom properties cascade to descendants — components that read `var(--color-*)` resolve correctly in both modes. However, `getComputedStyle(document.documentElement)` reads from `<html>` (not `.dark`) and returns light values even in dark mode. The runtime-auditor's Phase 0.5 drift-check script has been updated to read from `document.body` so the cascade from `.dark` is included.

---

## Recommended next steps

1. **Fix MAJOR-2 first (focus rings on `.btn-project`)** — this is a WCAG 2.4.13 keyboard accessibility blocker. Add `:focus-visible { box-shadow: 0 0 0 2px var(--color-surface-default), 0 0 0 4px var(--color-border-action); outline: none; }` to the `.btn-project` rule in `frontend/web/styles/project/_buttons.scss`. This is a single targeted fix.
2. **Fix MAJOR-1 and MAJOR-3 together** — both live in `PanelSearch.tsx`. The `title` prop should render as `<h1>` (or `<h2>` for legacy consistency) using `$h2-font-size` typography. The descriptor element should be a `<p>` using `color: var(--color-text-secondary)`. Fixing the heading tag will also resolve MINOR-6 (ratio).
3. **Fix MAJOR-5 (logo link accessible name)** — add `aria-label="Flagsmith home"` to `a[data-test="home-link"]` or `alt="Flagsmith"` to its `<img>`. Single-line fix in the top navigation component.
4. **Fix MAJOR-6 (GitHub icon dark mode)** — change `fill="#000000"` to `fill="currentColor"` in the GitHub icon SVG, and address all remaining hard-coded SVG fills via the static auditor (route to `design-auditor` against `frontend/web/components/` for the nav icon components containing `fill="#9DA4AE"` and `fill="#656d7b"`).
5. **Address MINOR-4 globally (motion tokens)** — route to `token-fixer` against `_buttons.scss`, any file using `transition: all`, and the input CSS — replace `0.15s ease-in-out` with `var(--duration-fast) var(--easing-standard)`, remove `transition: all` occurrences, and enumerate specific CSS properties instead. This is a mechanical substitution with no visual impact but brings the codebase in line with the token system.
