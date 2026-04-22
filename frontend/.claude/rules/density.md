# Rule: density — comfortable, default, compact (Flagsmith)

Flagsmith is a **comfortable-default** system. Where the Obsidian/Linear tradition anchors at 32px rows / 32px buttons, Flagsmith's buttons are 44px and tables run ~40px. Density is defined around that baseline, not against it.

This file specifies the three density modes, what triggers each, what changes, and how user-facing the control should be.

---

## 1. The three modes

### Comfortable (Flagsmith's default)

The baseline — what ships in every app shell unless explicitly overridden.

| Property | Value |
|---|---|
| Row height | 40px |
| Button default | 44px |
| Button `sm` | 40px |
| Input default | 40–44px |
| Sidebar item | 40px |
| Card padding | 24px |
| Section gap | 32px |
| Row text | 14/20 (`$font-size-base`) |
| Icon default | 18px |

### Default (denser, opt-in per surface)

For dashboards where data density matters more than reading comfort.

| Property | Value |
|---|---|
| Row height | 32px |
| Button default | 32px (`xsm`) |
| Input default | 32px |
| Sidebar item | 36–40px (unchanged — sidebar stays comfortable) |
| Card padding | 16px |
| Section gap | 24px |
| Row text | 14/20 |
| Icon default | 16px |

### Compact (extra-dense, rare)

For **data-heavy** views only — long event logs, keyword grids, reconciliation tables.

| Property | Value |
|---|---|
| Row height | 28px |
| Button default | 28px |
| Input default | 28px |
| Sidebar item | 36–40px (unchanged) |
| Card padding | 12px |
| Section gap | 20px |
| Row text | 13/18 (`$font-caption`) |
| Icon default | 16px (unchanged — a11y floor) |

### Reconciliation with typography.md

**Density does not invent new font sizes.** Flagsmith's typography scale is frozen: 11, 12, 13, 14, 16, 18, 24, 30, 34, 42. Density switches *between* existing scale tokens.

- Compact rows use 13/18 (`$font-caption`) — same size as table cells / sidebar items.
- Default and comfortable rows use 14/20.
- Comfortable expresses itself through **spatial breathing room**, not bigger text. Larger row heights and padding deliver the "comfort"; the text stays at the product's reading size.

This means a density toggle swaps row-height / padding / gap — and, for row-text specifically, toggles between 14 and 13. It never reaches for an off-scale size like 15px.

### What density does NOT change

- **Radii** (`var(--radius-md)` for controls, `var(--radius-lg)` for cards — constant across modes).
- **Border widths** (1px default, 2px for emphasis).
- **Focus ring** (2px `var(--color-border-action)`, 2px offset).
- **Typography line-height ratios** (always on the 4px grid).
- **Brand tokens** (`var(--color-surface-action)`, semantic colours).
- **Alpha values**.
- **Motion durations and easings**.
- **Page horizontal padding** (viewport governs this, not density).
- **Typography scale** (no off-scale font sizes).

---

## 2. What triggers each mode

Density is contextual, not a universal toggle.

### Per-surface default (automatic)

| Surface type | Default mode |
|---|---|
| Settings, preferences, account management | Comfortable |
| Authentication, onboarding | Comfortable |
| Main dashboard (KPIs + charts + primary table) | Comfortable or Default, designer's call |
| Data-heavy exploration (full-screen grid, long logs) | Compact |
| Modal dialogs | Inherited from page |
| Mobile viewport of any surface | Comfortable (touch targets) |

Density is determined by the **purpose of the surface**.

### Per-surface override (rare)

A specific region may override where the data demands it — e.g., an audit log inside Settings should be compact because the user scans hundreds of entries.

**Rule.** Overrides declared at the surface level via `data-density="..."` on the container. Documented in the component's spec. Never applied mid-page.

### User preference (optional)

A user-facing density toggle is optional and only appropriate when:

1. The product is primarily data-exploration.
2. Users span multiple screen sizes / accessibility needs.
3. The toggle persists per-user.

If only one is true, don't ship the toggle.

When shipped:

- Located in user preferences, not in the page header.
- Labels: "Compact" / "Default" / "Comfortable" — in that order.
- **Default selection is "Comfortable"** — Flagsmith's baseline. Users who prefer denser views can switch themselves.
- Applies only to surfaces that support density override — auth pages, modals, marketing stay on their intended mode.

---

## 3. Implementation

Density is a discrete token set swapped via `data-density` on a scope, not a scalar multiplier:

```scss
// Base tokens (comfortable — Flagsmith default)
:root {
  --control-h-md: 44px;
  --row-h-default: 40px;
  --card-padding: 1.5rem;    // 24px
  --section-gap: 2rem;       // 32px
  --row-text-size: #{$font-size-base};  // 14
}

[data-density="default"] {
  --control-h-md: 32px;
  --row-h-default: 32px;
  --card-padding: 1rem;      // 16px
  --section-gap: 1.5rem;     // 24px
}

[data-density="compact"] {
  --control-h-md: 28px;
  --row-h-default: 28px;
  --card-padding: 0.75rem;   // 12px
  --section-gap: 1.25rem;    // 20px
  --row-text-size: #{$font-caption};  // 13
}
```

Usage:

```html
<html data-density="comfortable">
  <div class="audit-log" data-density="compact">...</div>
  <section class="dense-dashboard" data-density="default">...</section>
</html>
```

### Why discrete, not a multiplier

- Row heights don't scale linearly — 40 × 0.8 = 32 is right, but 40 × 0.7 = 28 works only because predefined.
- Radii must NOT scale — `var(--radius-md)` looks right at every density.
- Border widths must NOT scale — 1px stays 1px.
- Typography stays on-scale — scaling 14 × 0.93 = 13 works because 13 already exists; scaling 14 × 1.07 = 15 breaks the scale.

---

## 4. Density + responsive interaction

When responsive and density rules conflict, **responsive wins at small viewports**:

| Viewport | Density behaviour |
|---|---|
| ≥`lg` (992) | Respect declared density |
| `md` – `lg` | Default mode at minimum (even if surface declares compact) |
| <`md` | Comfortable mode at minimum (touch targets) |

Compact rows at 375px wide are unreadable. Don't show them.

---

## 5. What changes when density changes

Updates:

- Row heights (tables, lists, menu items).
- Interactive control heights (buttons, inputs, selects).
- Card padding.
- Section gaps.
- Row text size (14 ↔ 13 between existing tokens).
- Icon sizes (16 default/compact; 18 comfortable).
- Sidebar item heights (only between default ↔ comfortable; compact keeps sidebar at default).

Does NOT update:

- Page title row (always `$h2-font-size`).
- Headings within content (mapped to role tokens regardless of density).
- Modal sizes (density affects contents, not widths).
- Focus rings, borders, radii.
- Colours, semantics, brand tokens.
- Overall typography scale — no off-scale sizes.

### What the auditor checks

- Declared density is one of `comfortable` / `default` / `compact` (auto — `data-density`).
- Computed row / button / input heights match declared density (auto).
- No computed `font-size` outside the scale {11, 12, 13, 14, 16, 18, 24, 30, 34, 42} regardless of declared density (auto — guards against 15px drift).
- Mid-page density switches flagged as suspicious (auto).
- **[runtime, multi-viewport]** at narrow viewports, density falls back per §4.
- **[manual review]** density choice matches surface purpose.

---

## Density auditor walk

1. **Identify declared density** per surface (`data-density`, or infer from surface type).
2. **Verify computed heights match** — buttons 44px comfortable, 32px default, 28px compact.
3. **Confirm no off-scale font sizes** are used.
4. **Check density choice matches surface purpose** — settings = comfortable; data exploration = compact; main dashboard = comfortable or default.
5. **At mobile viewport**, confirm density relaxes to at least default (no compact on touch).
6. **Flag density inconsistency** within a single page.
