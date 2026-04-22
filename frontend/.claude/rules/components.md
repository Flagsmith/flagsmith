# Rule: component specifications (Flagsmith)

Flagsmith's default button is 44px — the system is comfortable-mode-first. Where the source system anchored at 32px, Flagsmith anchors bigger. All values below match the actual SCSS in `web/styles/project/`.

## Buttons

Flagsmith's button height vars (`$btn-line-height*`): `xxsm` = 24px, `xsm` = 32px, `sm` = 40px, default = 44px, `lg` = 56px.

| Variant | Height | H-pad | Font | Radius |
|---|---|---|---|---|
| `xxsm` | 24px (floor — WCAG 2.5.8) | 12 | 13/18 500 | `var(--radius-sm)` (4) |
| `xsm` | 32px | 16 | 14/20 500 | `var(--radius-md)` (6) |
| `sm` | 40px | 16 | 14/20 500 | `var(--radius-md)` |
| **default** | **44px** | **20** | **14/20 600** | **`var(--radius-md)`** |
| `lg` | 56px | 24 | 16/24 600 | `var(--radius-lg)` (8) |

Note: `$btn-font-weight` is 700 in the current SCSS — a known legacy; use 600 on new variants.

**Variant mapping:**

| Variant | Background | Text | Border |
|---|---|---|---|
| Primary (CTA) | `var(--color-surface-action)` | `#fff` (or a fixed-contrast token) | none |
| Secondary | `var(--color-surface-subtle)` | `var(--color-text-default)` | 1px `var(--color-border-default)` |
| Ghost | transparent | `var(--color-text-default)` | none |
| Danger | `var(--color-surface-danger)` bold variant, or `$danger` solid | `#fff` | none |
| Selected | `var(--color-surface-action-subtle)` | `var(--color-text-action)` | 1px `var(--color-border-action)` |

Flagsmith has no pink/coral gradient. The primary-CTA brand moment is solid purple fill + `--color-surface-action-hover` on hover. Never use a gradient for primary CTA.

Icon-only buttons are square. `xxsm` 24×24 is the floor — never smaller.

## Inputs

Flagsmith's `$input-line-height` is 24px; actual box heights are derived from padding + line-height (roughly 36–44px depending on variant). Align new input variants to the button scale:

| Variant | Height | H-pad | Font | Radius |
|---|---|---|---|---|
| `sm` | 32px | 12 | 13/18 | `var(--radius-md)` |
| **default** | **40–44px** | **16** | **14/20** | **`var(--radius-md)`** |
| `lg` | 56px | 20 | 16/24 | `var(--radius-md)` |

- Background: `var(--color-surface-default)` (light) / `var(--color-surface-muted)` (dark) — handled by `$input-bg` / `$input-bg-dark`.
- Border: 1px `var(--color-border-default)` → `--color-border-strong` on hover → `--color-border-action` + 2px `--color-surface-action-subtle` ring on focus.
- Label: 14/20 weight 500, `var(--color-text-secondary)`, margin-bottom 6px.
- Helper text: 13/18 weight 400, `var(--color-text-secondary)`, margin-top 4px.
- Error text: 13/18 weight 500, `var(--color-text-danger)`.
- Field gap: 16px vertical. Label→input: 6px. Input→helper: 4px.

## Tables

| Density | Row H | V-pad | H-pad | Header font | Body font |
|---|---|---|---|---|---|
| Compact | 32 | 6 | 12 | 11/16 600 UPPERCASE | 13/18 |
| **Default** | **40** | **10** | **16** | **13/18 500** | **14/20** |
| Roomy | 48 | 12 | 16 | 14/20 500 | 14/20 |

- Container: `var(--color-surface-subtle)` + 1px `var(--color-border-default)` rim + `var(--radius-lg)`.
- Header: `var(--color-surface-muted)`, 1px `var(--color-border-default)` bottom, sticky, `var(--color-text-secondary)`.
- Numeric cells: **right-aligned**, **`tabular-nums`**, no exception.
- Row separation: 1px `var(--color-border-default)` bottom. **Dividers XOR zebra — never both.**
- Hover: `var(--color-surface-hover)` overlay, `var(--duration-fast)`.
- Selected: `var(--color-surface-action-subtle)` bg + 2px `var(--color-border-action)` inline-start bar.

## Cards

| Variant | Padding | Radius | Treatment |
|---|---|---|---|
| Compact | 12 | `var(--radius-md)` | 1px `var(--color-border-default)`, no shadow |
| **Default** | **16–24** | **`var(--radius-lg)`** | **`var(--color-surface-subtle)` + 1px `var(--color-border-default)`** |
| Roomy | 24 | `var(--radius-lg)` | `var(--color-surface-subtle)` + 1px `var(--color-border-default)` |
| Elevated | 16–24 | `var(--radius-lg)` | + `var(--shadow-sm)` |

- Title: 18/28 weight 600 (`<h5>`), `var(--color-text-default)`.
- Subtitle: 13/18 in `var(--color-text-secondary)`.
- Internal stack: 12px title→body, 16px body→footer.

## KPI cards

Vertical: **Label → Value → Delta → Sparkline (optional)**.

- Label: 11/16 weight 600 +0.08em UPPERCASE, `var(--color-text-secondary)`, margin-bottom 8.
- Value: 30/36 weight 600 `tabular-nums`, `var(--color-text-default)`, margin-bottom 4.
- Delta: 13/18 weight 500 `tabular-nums`. Positive → `var(--color-text-success)`. Negative → `var(--color-text-danger)`. Zero → `var(--color-text-secondary)`. **Always paired with sign and arrow.**
- Sparkline: 48px tall, 1.5px stroke, `var(--color-chart-1)` (blue — Flagsmith's default single-series).
- Card: `var(--color-surface-subtle)`, 16–24px padding, `var(--radius-lg)`, min-height 112 (172 with spark).
- Grid: `repeat(auto-fit, minmax(240px, 1fr))`, `gap-3` (16px).

## Modals

Flagsmith spec (from `_variables.scss`): `$modal-sm: 500px`, `$modal-md: 620px`, `$modal-lg: 900px`, `$modal-border-radius: 18px`, header padding `$spacer` / `$spacer * 1.5` (16/24), body padding `$spacer * 1.5` (24).

| Size | Max-width | Padding | Radius |
|---|---|---|---|
| sm | 500 | 24 | `var(--radius-2xl)` (18) |
| **md** | **620** | **24** | **`var(--radius-2xl)`** |
| lg | 900 | 24 | `var(--radius-2xl)` |

- Background: `var(--color-surface-default)` (light) / `var(--color-surface-subtle)` (dark). Border: 1px `var(--color-border-default)`. Shadow: `var(--shadow-xl)`.
- Overlay: `$modal-backdrop-bg` (~0.87 alpha black) + optional `backdrop-filter: blur(4px)`.
- Enter: `var(--duration-slow)` `var(--easing-entrance)` (scale 0.96→1 + opacity 0→1). Exit: `var(--duration-normal)` `var(--easing-exit)`.
- Focus trap required. **Modal inside a modal is forbidden.**

## Tooltips

- Max-width 280px. Padding 8×10 (single line) or 10×12 (multi-line).
- Font: 12/16 weight 400.
- Background: inverse of surface — dark background in light mode, light background in dark. Use `var(--color-surface-emphasis)` variant that flips correctly, or `$tooltip-bg` if established.
- Radius: `var(--radius-sm)`. Offset from trigger: 6px.
- Show delay: 500ms hover, 0ms keyboard focus. Hide delay: 0ms.
- `role="tooltip"` + `aria-describedby`. Escape dismisses (WCAG 1.4.13).

## Sidebar

- Width: 240px expanded (default), 56px collapsed.
- Background: `var(--color-surface-subtle)` or a dedicated shell token — one step from `--color-surface-default`.
- Item height: 36–40px (matches Flagsmith's comfortable default; 32px only in an explicit compact mode).
- Item font: 14/20 weight 400 default; 600 when active.
- Item radius: `var(--radius-md)`, inset 4px from sidebar edges.
- **Active state (brand moment):** `var(--color-surface-action-subtle)` bg + `var(--color-text-action)` label weight 600 + 2px `var(--color-border-action)` inline-start bar. (See `web/styles/project/_sidebar.scss`.)
- Hover: `var(--color-surface-hover)` overlay, no bar.
- Section label: 11/16 weight 600 UPPERCASE, `var(--color-text-secondary)`, 8×12 padding.

## Top header

- Height: 48–56px. Consistent across pages within the shell.
- Background: `var(--color-surface-default)`. Border: 1px `var(--color-border-default)` bottom.
- H-padding: match page gutter.
- Internal icons: 32×32 buttons in `var(--color-icon-secondary)`.

## Toasts

- Width 360px. Padding 12×14. Radius `var(--radius-md)`.
- Background: `var(--color-surface-subtle)`. Border: 1px `var(--color-border-default)`. Shadow: `var(--shadow-lg)`.
- Title: 14/20 weight 500. Description: 13/18 weight 400, `var(--color-text-secondary)`.
- Action: 14/20 weight 500, `var(--color-text-action)`.
- Position: bottom-right, 16px inset.
- Default duration 5000ms. 4000ms neutral. 8000ms error. Infinite for Undo.
- Enter `var(--duration-normal)` `var(--easing-entrance)` slide+fade. Exit `var(--duration-fast)` `var(--easing-exit)`.
- Semantic variants: 3px `var(--color-border-{semantic})` left bar in place of rim.

## Dropdowns and menus

- Item height: 32–40px (match the page's density).
- Item H-padding: 12–16.
- Item font: 14/20 weight 400; selected 500.
- Hover: `var(--color-surface-hover)`.
- Leading icon 16px + 8px gap. Trailing shortcut 12/16 `var(--color-text-secondary)`.
- Container: 4px padding (menu) / 12px (content). `var(--radius-lg)` for popovers, `var(--radius-md)` for menus.
- Background: `var(--color-surface-subtle)`. Border: 1px `var(--color-border-default)`. Shadow: `var(--shadow-md)`. Offset: 6px.

## Forms: checkboxes, radios, switches

- Checkbox: 16×16. Radius `var(--radius-sm)`. Border 1.5px `var(--color-border-strong)`. Checked: `var(--color-surface-action)` bg + white check 12px. Hit target wrapped to 24×24 via label padding.
- Radio: 16×16 circle. Inner dot 6×6 `var(--color-surface-action)` when checked.
- Switch: track 32×18. Thumb 14px white. Radius `var(--radius-full)`. On-track `var(--color-surface-action)`. 160ms ease.

## Tabs

Two sanctioned variants: **pill** (primary) and **sub** (nested/secondary). Never nest pill-in-pill.

### Pill (primary — `variant="pill"`) — default for in-page tab navigation

- Container: inline-flex on `var(--color-surface-muted)` tray, `var(--radius-md)`, 3px padding.
- Item height: ~36px. Font: 13/18.
- Item padding: 8px × 24px.
- Inactive: transparent bg, `var(--color-text-secondary)`, weight 400. Hover: `var(--color-text-default)`.
- Active: `var(--color-surface-action)` fill, white text, weight 600.

### Sub (secondary/nested — `variant="sub"`)

- Container: inline-flex, no tray chrome, 4px gap between items.
- Item height: ~26px. Font: 12/16 weight 500.
- Item padding: 4px × 12px. Radius `var(--radius-sm)`.
- Inactive: transparent bg, `var(--color-text-secondary)`. Hover: `var(--color-text-default)` + `var(--color-surface-hover)`.
- Active: `var(--color-surface-action-subtle)` bg, `var(--color-text-default)` weight 600.

### Variant-hierarchy rule

- One level of tabs on a page → `pill`.
- Two levels → outer `pill`, inner `sub`. Never two nested pills.
- Three levels → stop and reconsider the IA.

### What the auditor checks

- No primary CTA uses a gradient background (auto).
- Tab rows use pill or sub, not a legacy underline variant in new code (auto).
- When a page has two tab rows, the inner row is `sub` (auto — DOM check).

## AI summary blocks (proposal)

Flagsmith does not yet have an established AI-summary pattern. If introduced, the anatomy is:

- Tint: `var(--color-surface-info)` (blue-tinted) OR `var(--color-surface-action-subtle)` (purple-tinted) — pick one and use consistently.
- Required signals (all three): tinted background, sparkle icon, "AI summary" label.
- Body: 14/20 line-height 1.6 (looser than default).
- Body text colour: `var(--color-text-default)` full contrast — **never secondary**.
- Citations: `var(--color-text-action)` at 10px weight 500, small tinted badge.
- Disclaimer: 11/16 `var(--color-text-secondary)`, info icon, text "AI-generated. Verify important details." Always present.
