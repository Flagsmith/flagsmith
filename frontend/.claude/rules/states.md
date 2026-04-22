# Rule: states — loading, empty, error, hover, active, disabled, selected (Flagsmith)

Every content region, every interactive element, and every data-bearing surface has at least four states. Most bugs live in the three non-default states that were never designed.

Rules apply across light and dark modes — use semantic CSS vars throughout so both modes work from one rule.

Rules marked **[manual review]** cannot be auto-checked.

---

## 1. Loading states (four thresholds)

Match the loading treatment to the expected duration.

| Duration | Treatment | Why |
|---|---|---|
| <100ms | No indicator | Below human perception threshold |
| 100–300ms | No indicator (delay spinner render by 300ms) | Prevents flash-flicker |
| 300ms – 1s | Inline spinner or minimal skeleton | User noticed the wait |
| 1–3s | Skeleton matching final layout | User needs confidence the page is working |
| 3–10s | Determinate progress bar with status text | User needs to see progress |
| >10s | Progress bar + phase + cancel button | User might leave or cancel |

### 1.1 Skeleton pattern

```scss
.skeleton {
  background: var(--color-surface-muted);
  border-radius: var(--radius-xs);
  animation: skeleton-shimmer 1800ms linear infinite;
}

@keyframes skeleton-shimmer {
  0%   { opacity: 0.6; }
  50%  { opacity: 1.0; }
  100% { opacity: 0.6; }
}
```

Using `--color-surface-muted` makes the skeleton read correctly in both modes: on light it's a pale grey, on dark it's a dim panel — both differ from `--color-surface-default` by one visible step.

**Structural rules:**

1. **Skeletons match final dimensions.** Height, width, radius, line count.
2. **Skeleton line widths vary** — 100%, 92%, 68% for three lines of text. Uniform lines read as a loading bar.
3. **Skeletons have a cap.** Never more than 3 skeleton rows for a list of unknown length. Fade a 4th at 50% opacity.
4. **Shimmer duration is 1800ms** (literal — see `motion.md`).
5. **Heading and descriptor of the region are NOT skeletons.** Only the data-bearing content is skeletonised.
6. **Tables have one skeleton row per data row**, up to 3. Table header renders as real text.

### 1.2 Spinner pattern

| Context | Size | Stroke | Colour |
|---|---|---|---|
| Inline with text | 14px | 2px | current colour (inherit) |
| Button (replaces leading icon) | 14–16px | 2px | current colour (inherit) |
| Standalone (page centre) | 24px | 2.5px | `var(--color-border-action)` |
| Full-page overlay | 32px | 3px | `var(--color-border-action)` |

Rotation: 800ms `linear` infinite. `role="status"` + visually-hidden "Loading".

### 1.3 Contextual loading text

Phase cycles at 3s intervals:

> "Thinking…" → "Reading sources…" → "Summarising…" → "Checking citations…"

**Rules:**

1. Phase labels are descriptive, not decorative.
2. Phase labels use 13/18 `var(--color-text-secondary)`.
3. Phases cycle at 3s; the last phase is sticky.
4. When a loader runs >10s, append "This is taking longer than usual. [Cancel]" below the phase label.

### 1.4 Timeout behaviour

- **<3s expected**: timeout at 5s → error state.
- **3–10s expected**: timeout at 15s → error state with "Still waiting — retry?".
- **>10s expected**: no timeout, but cancel button required.

### What the auditor checks

- Skeleton dimensions match eventual content (runtime DOM comparison) (auto).
- Skeleton shimmer is 1800ms (auto).
- Skeleton background resolves to `var(--color-surface-muted)` (auto).
- Spinner rotation is 800ms (auto).
- **[manual review]** phase labels descriptive.
- **[manual review]** loader has a timeout path.
- Any spinner on an operation documented as <300ms is a finding (auto).

---

## 2. Empty states

Empty states appear when a region has no data. **Not errors** — they describe a legitimate condition the user can act on.

### Anatomy

```
[icon]                              ← optional, small
[heading]
[descriptor / what this is]
[primary action]                    ← optional
[secondary link]                    ← optional
```

### Spec

| Slot | Token | Colour |
|---|---|---|
| Icon (optional) | 24–32px | `var(--color-icon-secondary)` |
| Heading | `$h5-font-size` (18/28 600) | `var(--color-text-default)` |
| Descriptor | 14/20 | `var(--color-text-secondary)`, `max-width: 48ch` |
| Primary action | Default button (44px) | per button spec |
| Secondary link | 13/18 weight 500 | `var(--color-text-action)` |

Layout:
- Centred horizontally.
- 48px vertical padding (more generous than default).
- 12px icon→heading; 8px heading→descriptor; 16px descriptor→action.

### Writing rules

1. Explain what would be here — not just "No results." → "No flags yet. Create one to start rolling out features."
2. Suggest a next action — primary CTA matches the first thing a user would do.
3. Match heading to context — empty table inside a card gets a card-level empty state.
4. Sentence case.
5. No apologies.

### Variants by cause

| Cause | Heading | Descriptor | Action |
|---|---|---|---|
| Never created | "No X yet" | "X help you do Y. Get started by Z." | Primary: "Create X" |
| Filtered out | "No X match your filters" | "Try broadening the date range or clearing filters." | Secondary: "Clear filters" |
| Search no results | "No results for '[query]'" | "Check spelling or try different terms." | — |
| Not yet active | "X will appear here once Y" | "Y typically happens within Z." | Secondary: "Learn more" |

**Auditor proxy**: an empty state with heading matching `/^no (data|results|items|records)\.?$/i` and no cause-specific wording is a finding.

### What the auditor checks

- Empty state has heading + descriptor minimum (auto).
- Heading in sentence case (auto).
- Descriptor within 48ch width (auto).
- Primary action present where a next step exists (auto).
- **[manual review]** copy addresses the specific cause.
- Generic "No data" headings flagged `minor` `medium`.

---

## 3. Error states

Something failed. Distinct from empty.

### Anatomy

```
[icon: ⚠ or ✕ in var(--color-icon-danger)]
[heading: what failed]
[descriptor: why, if known]
[primary action: retry / dismiss / go back]
[secondary: contact support / view details]
```

### Spec

| Slot | Token | Colour |
|---|---|---|
| Icon | 20–24px | `var(--color-icon-danger)` |
| Heading | `$h6-font-size` (16/24 600) | `var(--color-text-default)` |
| Descriptor | 14/20 | `var(--color-text-secondary)` |
| Primary action | Default button, **secondary** variant (NOT danger — action is "retry", not "destroy") | per spec |
| Details (expandable) | monospace inside a collapsible | `var(--color-text-secondary)` |

### Variants by scope

| Scope | Treatment |
|---|---|
| Field-level error | Inline below the input, 11/16 `var(--color-text-danger)`, red border |
| Section-level error | Replaces section content, preserves heading/descriptor above |
| Page-level error | Replaces main content, preserves page title row |
| App-level error (crash) | Full-page error boundary, minimal chrome |

### Writing rules

1. Explain what happened before suggesting what to do.
2. Never blame the user for server errors.
3. Include error code / reference in expandable details.
4. Retry is the default action.
5. Match severity to scope.

### What the auditor checks

- Error has icon, heading, descriptor (auto).
- Icon uses `var(--color-icon-danger)` (auto).
- Primary action button is NOT the danger variant (auto — danger background on the retry button is a finding).
- **[manual review]** copy doesn't blame the user.
- **[manual review]** severity matches scope.

---

## 4. Hover states (non-button composites)

| Pattern | Hover treatment |
|---|---|
| Table row | Background overlay `var(--color-surface-hover)`, 80ms |
| Card (clickable) | Background to `var(--color-surface-hover)` overlay, cursor pointer, border may brighten to `--color-border-strong`, 120ms |
| Card (static) | No hover change. Period. |
| Nav item | Background fills to `var(--color-surface-hover)`, 120ms |
| Chart data point | Point scales 3→5px, tooltip appears, 120ms |
| Sidebar item | Background fills to `var(--color-surface-hover)` (or brand-tinted overlay per `_sidebar.scss`), 120ms |
| KPI tile (clickable) | Border brightens to `--color-border-strong`, optional `--shadow-sm`, 120ms |
| KPI tile (static) | No hover. |

### Rules

1. **Static elements do not hover.** Hover implies interactivity.
2. **Hover is reversible in a single frame.** No staggered animations, no morphing layouts.
3. **Cursor state accompanies hover** — `cursor: pointer` on every hoverable.
4. **Hover does not move layout.** Never change padding, margin, or dimensions on hover.
5. **Hover effect is a background tint, colour shift, or border shift** — not a shadow change.

### What the auditor checks

- Every element with a hover effect also has `cursor: pointer` (auto).
- Static elements without `onClick` / `href` / `role="button"` don't have hover effects (auto).
- Hover transitions ≤200ms (auto).
- Hover does not change `padding`, `margin`, `width`, `height` (auto).
- No shadow changes on hover (auto).

---

## 5. Active / pressed states

### Spec

| Element | Active treatment | Duration |
|---|---|---|
| Button (solid primary) | Background → `var(--color-surface-action-active)` | 80ms `var(--easing-exit)` |
| Button (secondary) | Background → `var(--color-surface-active)` overlay | 80ms |
| Button (ghost) | Background → `var(--color-surface-active)` overlay | 80ms |
| Table row (clickable) | Background → `var(--color-surface-action-subtle)` briefly | 80ms |
| Menu item | Same as ghost button active | 80ms |

### Rules

1. **Active is 80ms** — faster than any other transition.
2. **Active never translates Y.** No "button press down" — consumer-app pattern, feels toy-like.
3. **Active is distinct from selected.** Active is the moment of pressing; selected persists.

### What the auditor checks

- Active duration is 80ms (auto).
- No `transform: translateY` in `:active` (auto).
- Selected and active have distinct styles (auto).

---

## 6. Disabled states

### Spec

| Treatment | Value |
|---|---|
| Opacity | 0.4 |
| Cursor | `not-allowed` |
| Pointer events | Retained (so tooltips still work) |
| Hover change | None |
| Focus | Reachable via keyboard if the control has a reason to announce |

### Rules

1. **Disabled has a reason, and the user can see it.** Every disabled control has a tooltip or inline text.
2. **Disabled is not the same as hidden.** If the user should never see this action, remove it.
3. **Disabled isn't used for "not yet implemented"** — that's a feature flag.

### What the auditor checks

- Disabled opacity resolves to 0.4 (auto).
- Disabled has `cursor: not-allowed` (auto).
- Disabled elements have a `title`, adjacent helper text, or `aria-describedby` explanation (auto proxy, `medium`).

---

## 7. Selected / active-item states

### Spec

| Element | Selected treatment |
|---|---|
| Table row | `var(--color-surface-action-subtle)` background, 2px `var(--color-border-action)` inline-start bar |
| Tab (pill) | `var(--color-surface-action)` fill, white text, weight 600 |
| Tab (sub) | `var(--color-surface-action-subtle)` bg, text weight 600 |
| Sidebar item | `var(--color-surface-action-subtle)` bg, `var(--color-text-action)` label weight 600, 2px `var(--color-border-action)` inline-start bar |
| Menu checkbox item | `var(--color-surface-action-subtle)` bg, `var(--color-icon-action)` checkmark |
| Segmented control thumb | `var(--color-surface-subtle)` fill, `var(--shadow-sm)`, `var(--radius-sm)` |

### Rules

1. **Selected always has a non-colour affordance.** Colour alone fails WCAG. Tab selection pairs with fill or bottom border; row selection with left bar; menu selection with checkmark.
2. **Only one item selected at a time** in single-select contexts.
3. **Selected persists through hover.** Selected-hover is distinct from selected-default — typically a deeper tint (`var(--color-surface-action-muted)`).

### What the auditor checks

- Selected states include a non-colour affordance (auto).
- Only one item selected per `role="tablist"` / `role="radiogroup"` / `<nav>` (auto).
- Selected-hover is distinct from selected-default (auto).

---

## State auditor walk

1. Default — covered by component specs.
2. Loading — exercise every data-bearing region; check skeleton/spinner match duration category.
3. Empty — force empty via filter; check heading + descriptor + cause-appropriate copy.
4. Error — trigger a failure; check retry flow.
5. Hover — hover every interactive element; check transitions, cursor, no layout jumps.
6. Active — click; check 80ms response, no translateY.
7. Disabled — find disabled elements; check explanation is available.
8. Selected — check non-colour affordance and single-selection rule.

Confidence:

- **High**: structural or measurable.
- **Medium**: pattern match (generic empty heading, error doesn't suggest retry).
- **Low**: [manual review] copy tone.
