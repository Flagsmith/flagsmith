# Rule: accessibility floor (Flagsmith)

Non-negotiable minimums. Violating any of these is a bug, not a style choice. Rules apply in both light and dark mode.

## Target size (WCAG 2.5.8 AA)

- **Minimum: 24×24 CSS px.** The `xxsm` button (24px) is the floor. Primary actions 40–44px — Flagsmith's default button is 44px, comfortably above the AAA 44×44 target-size bonus.
- Icon-only buttons respect the same minimum. Inline wrap with padding if the visible glyph is smaller.

## Focus (WCAG 2.4.13)

- **2px minimum perimeter** around the focused element.
- **2px offset** between the element and the ring.
- **3:1 contrast** against adjacent pixels on both sides in both light and dark mode.
- Token: `var(--color-border-action)` (purple-600 light / purple-400 dark) satisfies 3:1 against every surface in the system.
- Implementation: `box-shadow: 0 0 0 2px var(--color-surface-default), 0 0 0 4px var(--color-border-action)` — double-ring guarantees visibility against both modes.
- Always use `:focus-visible`, never bare `:focus`. Mouse users should not see rings.
- High-contrast fallback: `@media (forced-colors: active) { outline: 2px solid CanvasText; }`.
- **`outline: none` without a replacement is forbidden.**

## Text contrast (WCAG 1.4.3 AA)

- Normal text ≥ 4.5:1. Large text (≥18px, or ≥14px bold) ≥ 3:1.
- `var(--color-text-default)` on `var(--color-surface-default)`: ~13:1 light, ~15:1 dark. Clear AAA — use this for body.
- `var(--color-text-secondary)` on `var(--color-surface-default)`: ~5.2:1 light, ~6:1 dark. Passes AA for body.
- **`var(--color-text-tertiary)` is below 4.5:1** in light mode (~3.8:1). **Never on body text.** Decorative meta only (axis ticks, timestamps in low-priority contexts).
- **Warning and info text at body size fail AA in light mode** (`--color-text-warning` ~3.5:1, `--color-text-info` ~3.6:1). Pair with an icon + label at body size, or render on the matching `--color-surface-warning` / `--color-surface-info` tinted fill where large-text 3:1 applies.

## Non-text contrast (WCAG 1.4.11)

- UI borders, icons, and chart elements that carry meaning ≥ 3:1.
- `var(--color-border-default)` is decorative — use `var(--color-border-strong)` where a border carries meaning.
- `var(--color-border-disabled)` (~8% alpha) is below 3:1 by design — never as sole separation.

## Colour never alone (WCAG 1.4.1)

- Every semantic colour pairs with an icon, sign, or text.
- Deltas: `+4.2% ▲` or `−1.8% ▼`. Sign + arrow always.
- Status badges: fill + icon + label.
- Red/green pairs include direction indicator.

## Motion (WCAG 2.3.3 AAA)

- `prefers-reduced-motion` honoured everywhere. Transforms / parallax / shimmer disabled. Opacity fades preserved at ≤120ms. See `motion.md`.

## Focus not obscured (WCAG 2.4.11)

- Apply `scroll-padding-top` equal to the sticky header height on scroll containers.
- Toasts must not cover interactive regions.

## Zoom (WCAG 1.4.4)

- 200% zoom must not break layout. No fixed pixel widths on text containers.

## Keyboard navigation (WCAG 2.1.1)

- Every action reachable via Tab / Shift-Tab / arrows / Enter / Escape.
- Skip-link at page top.
- Focus trap inside modals.
- `aria-live` regions for async updates.
- Escape dismisses modals, popovers, tooltips.

## Labels and names (WCAG 4.1.2)

- **Icon-only buttons require `aria-label`.** Always.
- **Truncated text requires a tooltip or expand affordance.** Silent data loss is a bug.
- Every form input has a `<label>` or `aria-labelledby`.

## Common violations

- `:focus { outline: none; }` with no replacement — breaks keyboard users.
- Icon buttons without `aria-label`.
- Status using colour alone (green dot with no "Active" label, red text with no × icon).
- `text-overflow: ellipsis` with no title or tooltip.
- Modal without focus trap.
- Toast covering a sticky action bar.
- Muted text below 3:1 contrast (disabled is the only exemption).
- `var(--color-text-tertiary)` on a body paragraph — promote to `--color-text-secondary`.
- Warning / info text at body size on `--color-surface-default` without an icon or tinted fill.
