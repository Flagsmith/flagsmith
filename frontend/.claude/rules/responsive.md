# Rule: responsive — breakpoints, reflow, multi-viewport (Flagsmith)

Desktop-first, but every page must work on tablet and mobile. Breakpoints follow Bootstrap 5 defaults as wired in `_variables.scss`.

Rules marked **[manual review]** cannot be auto-checked.

---

## 1. Breakpoints (Bootstrap 5)

```scss
// from _variables.scss
$grid-breakpoints: (
  xs: 0,
  sm: 544px,
  md: 768px,
  lg: 992px,
  xl: 1200px,
  xxl: 1400px,
);
```

Name breakpoints by **what changes at that size**, not the device:

```scss
// Good — names the intent
@media (min-width: map-get($grid-breakpoints, md)) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

// Avoid — names the device
@media (min-width: 768px) {  // "tablet-ish"
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
```

### Default behaviour across breakpoints

- **Page horizontal padding**: consistent at every breakpoint within the shell. Whatever the shell picks (typically 16–24px), don't vary it per-page.
- **Content max-width**: 1440px for dashboards, 720px for forms, 65ch for prose. Applied at every size; narrow viewports fill available width up to these caps.
- **Sidebar** (`web/styles/project/_sidebar.scss`): expanded at desktop. Flagsmith's current sidebar collapse behaviour is handled app-side (`<AppNav>`) rather than a pure CSS media query — confirm per-component. Typical pattern: collapse to icon-only at `md` (768px); drawer with backdrop below `sm` (544px).
- **Top header**: constant height across breakpoints. Secondary nav (breadcrumbs, tabs on second row) may hide below `md`.

---

## 2. Reflow patterns

### 2.1 Grid reflow

Default: `repeat(auto-fit, minmax(<min>, 1fr))`. Reflows automatically without media queries.

| Content | min | Behaviour |
|---|---|---|
| KPI cards | 240px | 4-across → 2-across → 1-across |
| Dashboard tiles | 320px | 3-across → 2-across → 1-across |
| Card grid (denser) | 200px | 6-across → ... → 1-across |

**Rule.** Prefer `auto-fit` over explicit media-query column counts unless the behaviour must differ from the automatic collapse.

### 2.2 Sidebar + content reflow

- Desktop: `[sidebar 240px] [content fluid to 1440px]`.
- At `md`: `[sidebar 56px collapsed] [content]`.
- At `sm` and below: `[hamburger, sidebar hidden]`, sidebar reopens as a full-height drawer from left with backdrop.

### 2.3 Page title row reflow

| Viewport | Layout |
|---|---|
| Desktop | `[title] [chips] ────── [actions]` |
| `md` / tablet | Title + actions row 1; chips row 2 |
| `sm` / mobile | Title + overflow menu (⋮) row 1; chips row 2; non-primary actions in menu |

**Rules:**

1. Title never shrinks below `$h5-font-size` (18px). Below `md` may step down from `$h2-font-size` to `$h4-font-size` to preserve layout — not below.
2. Chips wrap to row 2 below `md`, stack vertically below `sm` if >3 chips.
3. Actions collapse to overflow menu when >2 below `md`, or >1 below `sm`. Primary action stays visible.

### 2.4 Form reflow

Desktop forms often two-column; collapse to single at narrow widths.

```scss
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem 1rem;  // 16 row, 16 col
}
@media (max-width: map-get($grid-breakpoints, md)) {
  .form-grid { grid-template-columns: 1fr; }
}
```

Labels stay above fields across breakpoints.

### 2.5 Modal reflow

| Viewport | Treatment |
|---|---|
| ≥`md` | Modal centred, max-width per size (sm/md/lg) |
| <`md` | Full-width sheet, slides up from bottom |
| <`sm` | Full-screen, no backdrop (the sheet IS the screen) |

Header persists with increased touch targets (44px+ close button at mobile).

---

## 3. Component responsive rules

### Buttons

- Default 44px — already comfortably above touch-target floor across viewports.
- Secondary / `xsm` 32px buttons are desktop-ok; on `sm` viewports, bump to `sm` (40px) for primary CTAs if they currently render at 32px.
- Icon-only buttons never go below 32×32 on touch viewports.

### Inputs

- Desktop default 40–44px; stays there on mobile (the default is already touch-friendly).
- `sm` inputs (32px) bump to 40px on `sm` viewports.

### Tables

See `data-viz.md` §6 for the three narrow-viewport strategies.

### Charts

See `data-viz.md` §7.

### Toasts

- Desktop: 360px wide, bottom-right, 16px inset.
- Mobile: full-width minus 16px side margins, bottom-centre.

---

## 4. Viewport-specific patterns to avoid

### Fixed pixel widths on text containers

```scss
// Breaks at 200% zoom and narrow viewports
.description { width: 520px; }

// Scales
.description { max-width: 65ch; }
```

### Horizontal scroll on pages (not tables)

A page that scrolls horizontally at 375px is a bug. Tables scroll, pages don't.

### Hover-only affordances on touch

Touch devices don't hover. Every hover-triggered affordance must have a tap equivalent:

- Hover reveals "Delete" → on touch, button always visible (lower emphasis) or in an overflow menu.
- Hover shows tooltip → on touch, tap shows tooltip; tap again dismisses.

### Content reflowing into unreadable density

A 12-column table compressed into 1 column without a reflow strategy is unreadable. Every component needs a deliberate small-viewport design.

### What the auditor checks

- No fixed pixel widths on `<p>`, `<div>`, or content containers (auto).
- **[runtime, multi-viewport]** no horizontal page scroll at 375, 768, 1024.
- **[manual review]** hover-triggered affordances have touch equivalents.
- **[runtime, multi-viewport]** tables and charts remain readable per declared strategy.

---

## 5. Touch vs. pointer

Touch targets governed by `accessibility.md` — 24×24 minimum per WCAG 2.5.8, 44×44 preferred. Flagsmith's 44px default button already clears the preferred floor.

### Touch-specific rules

1. **Clickable rows on touch**: entire row is a tappable area, with visible indication (chevron, arrow, full-row press highlight). Inline links inside a clickable row conflict — pick one.
2. **Long-press menus** are valid for secondary actions, but must have a tap-visible equivalent (overflow menu) because long-press isn't discoverable.
3. **Swipe gestures** optional polish. Every swipeable action must have a visible button equivalent.
4. **Pull-to-refresh** permitted on primary lists; a refresh button must exist for non-touch users.

### What the auditor checks

- **[manual review]** touch-only gestures have visible button equivalents.
- **[runtime, multi-viewport]** interactive element sizes clear 44×44 preferred floor at mobile.

---

## 6. Testing viewports

The runtime auditor sweeps these sizes:

| Name | Width × height | Purpose |
|---|---|---|
| Mobile portrait | 375 × 812 | iPhone baseline |
| Mobile landscape | 812 × 375 | orientation flip |
| Tablet portrait | 768 × 1024 | iPad baseline |
| Laptop | 1280 × 800 | small MacBook |
| Desktop (default) | 1440 × 900 | comfortable desktop |
| Wide | 1920 × 1080 | big external |

**Minimum sweep**: 375, 768, 1440. Add 1920 if the app has known ultrawide issues.

### What the auditor evaluates across viewports

- No horizontal page scroll at any size (auto, runtime).
- Primary CTAs reachable at 44×44 on touch (auto, runtime).
- Text readable (not clipped, not obscured) (runtime).
- Sidebar transitions correctly at `md` and `sm` (runtime).
- Modals transition to sheets at narrow sizes (runtime).
- Tables apply declared narrow strategy (runtime).
- Forms collapse to single column (runtime).

---

## Responsive auditor walk

1. Load at desktop (1440), capture baseline.
2. Resize to tablet (768), capture, compare: sidebar collapsed? title row reflowed? forms single-column? tables applying strategy?
3. Resize to mobile (375), capture: sidebar drawer? touch targets ≥44×44? no horizontal page scroll? modals as sheets?
4. Report per-viewport findings — a layout issue at 375 is distinct from the same at 768.

Cross-viewport findings (bug everywhere) get consolidated. Viewport-specific findings stay separate.
