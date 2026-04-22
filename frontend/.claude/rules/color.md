# Rule: colour (Flagsmith — dual mode)

Light default, dark mode applied by `web/project/darkMode.ts` which puts `.dark` on `<body>` and `data-bs-theme="dark"` on `<html>` (persisted in `localStorage.dark_mode`). The token overrides are scoped under the `.dark { ... }` selector and cascade from body to all descendants. **Every colour decision must resolve via a semantic CSS custom property so it flips automatically.** A component that hard-codes a primitive is a bug in both modes — one today, one later.

British spelling in prose ("colour"); SCSS / CSS identifiers stay American ("color") because the codebase does.

## Surface stack

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-surface-default` | white | `$slate-950` | **Page background** |
| `--color-surface-subtle` | `$slate-50` | `$slate-900` | Cards, tables, KPI tiles (one step up from page) |
| `--color-surface-muted` | `$slate-100` | `$slate-850` | Recessed well, code block, secondary panel |
| `--color-surface-emphasis` | `$slate-200` | `$slate-800` | Inset / selected cell / strongest neutral fill |
| `--color-surface-hover` | 8% black | 8% white | Row / card hover (overlay, not a new surface) |
| `--color-surface-active` | 16% black | 16% white | Row / card pressed |
| `--color-surface-action` | `$purple-600` | `$purple-400` | **Primary CTA fill** |
| `--color-surface-action-subtle` | 8% purple | 8% white | Selected row, brand-tinted background |

**Rules:**

- Never use `#000`, `#fff`, `$slate-0`, or `$slate-1000` directly as a surface.
- Never stack three raised surfaces (`subtle` on `muted` on `default`) — it flattens in dark mode and looks busy in light. Use at most two elevation steps on a page.
- Elevation = surface-lightness shift + `--color-border-default` rim. Shadow is atmosphere, not structure (see `--shadow-*`).
- `--color-surface-hover` is an **overlay tint**, not a colour change. It stacks on whatever surface is below via `oklch(... / 0.08)`. Don't assign it as a `background`; use it with `background-color: var(--color-surface-hover)` on the hover state while the underlying surface keeps its identity.

## Background tints (semantic, no elevation)

Use for inline alerts, banners, brand moments — never as the default surface of a region.

| Token | Light | Dark |
|---|---|---|
| `--color-surface-action-subtle` | purple @ 8% | white @ 8% |
| `--color-surface-action-muted` | purple @ 16% | white @ 16% |
| `--color-surface-danger` | red @ 8% fill | darkened red fill |
| `--color-surface-warning` | orange @ 8% | darkened orange |
| `--color-surface-success` | green @ 8% | darkened green |
| `--color-surface-info` | blue @ 8% | darkened blue |

The dark-mode semantic backgrounds are NOT simple alpha — they're computed via `oklch(... L=0.18 ...)` for legibility on dark. Don't try to synthesise them in a component.

## Text tiers

| Token | Light (on surface-default) | Dark | Use |
|---|---|---|---|
| `--color-text-default` | #1a2634 ~13:1 | white ~15:1 | **Default body, table cells** |
| `--color-text-secondary` | #656d7b ~5.2:1 | #9da4ae ~6:1 | Labels, helper text, descriptors |
| `--color-text-tertiary` | #9da4ae ~3.8:1 | white @ 48% ~4.4:1 | Decorative meta — **never body text** |
| `--color-text-disabled` | — ~3:1 or below | — | Disabled controls only |
| `--color-text-action` | `$purple-600` ~7.1:1 | `$purple-400` ~5.8:1 | Links, brand text |
| `--color-text-danger` | `$red-500` ~4.8:1 | `$red-500` ~5.5:1 | Error copy, delta-negative |
| `--color-text-success` | `$green-500` ~4.8:1 | `$green-500` ~5.4:1 | Success copy, delta-positive |
| `--color-text-warning` | `$orange-500` ~3.5:1* | `$orange-500` ~4.2:1* | Warning (pair with icon) |
| `--color-text-info` | `$blue-500` ~3.6:1* | `$blue-500` ~4.5:1 | Info |

\* Warning and info in light mode are below 4.5:1 at body size. **Pair with icon + label, or render on `--color-surface-warning` / `--color-surface-info` tinted fills where the large-text 3:1 rule applies.** Raw `--color-text-warning` on `--color-surface-default` at 14px is a finding.

Headings (h1–h6) inherit `--color-text-default` by default. Don't override unless a heading is semantically coloured (`text-danger` for "Delete account" in a danger zone is fine).

## Borders

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-border-default` | slate-500 @ 16% | white @ 16% | **Default component edge — cards, inputs, buttons** |
| `--color-border-strong` | slate-500 @ 24% | white @ 24% | Input hover, strong dividers |
| `--color-border-disabled` | slate-500 @ 8% | white @ 8% | Disabled control |
| `--color-border-action` | `$purple-600` | `$purple-400` | **Focus ring, selected row bar, brand-emphasised edge** |
| `--color-border-danger` / `-warning` / `-success` / `-info` | semantic colour | semantic colour | Invalid input, banner edge |

**Rules:**

- `--color-border-default` is the baseline. Use it unless you have a reason.
- Focus rings use `--color-border-action`. See `accessibility.md`.
- Never use a text colour as a border (`color: $purple-600` applied to `border-color` is a smell — use `--color-border-action`).
- `--color-border-disabled` is decorative only; it's below 3:1. Don't rely on it as the sole separation.

## Brand (purple)

- **Primary CTAs** use `--color-surface-action` fill + `white` text (contrast checked in both modes). Never use `$slate-1000` as the CTA text colour — it won't read on dark-mode purple-400.
- **Focus rings** use `--color-border-action` (purple-600 light / purple-400 dark).
- **Selected sidebar item** uses `--color-surface-action-subtle` background + `--color-text-action` label + `--color-border-action` left bar.
- Flagsmith does NOT have a pink/coral gradient brand signature. The brand moment is the solid purple CTA and its hover shift.

## The "never colour alone" rule (WCAG 1.4.1)

Every semantic colour pairs with an icon, sign, or text label:

- Deltas: `+4.2% ▲` in `--color-text-success`, `−1.8% ▼` in `--color-text-danger`. Sign + arrow always.
- Status badges: fill + icon (✓ / ! / ✕ / ⓘ) + text label.
- Red/green pairs always include a direction indicator.
- Warning text at body size **must** be accompanied by an icon since the contrast floor is 3:1 (large-text rule) unless the surface is `--color-surface-warning`.

## Cross-mode gotchas

1. **Opacity alphas on `$slate-0` vs `$slate-1000`** — in light mode, hover overlays are black @ 8%; in dark, white @ 8%. The semantic tokens handle this. If you write `rgba(255,255,255,0.08)` directly, you get a translucent layer on light mode that hides behind the white surface and does nothing.
2. **Never use `$text-icon-light` (#ffffff) as the default body color in a component** — it breaks light mode silently. Use `--color-text-default`.
3. **Avoid `.dark` selectors in components** — if a colour doesn't look right in dark, fix the token, not the component. The exception: a mode-specific asset (SVG illustration), which can branch on `.dark` to swap the `src`.
4. **Alpha tokens** `$white-alpha-*` / `$black-alpha-*` exist for cases where you need a specific overlay, but a semantic token almost always exists — check first.

## Common violations (findings)

- `background: #ffffff` → `background: var(--color-surface-default)` (or `--color-surface-subtle` for cards).
- `color: #1a2634` → `color: var(--color-text-default)`.
- `color: $slate-600` in a component → `color: var(--color-text-default)`.
- `color: white` on body text → `color: var(--color-text-default)`.
- `border: 1px solid #e0e3e9` → `border: 1px solid var(--color-border-default)`.
- Primary CTA with `background: $primary` → should be `background: var(--color-surface-action)` unless the file is legacy-SCSS throughout.
- `.dark .my-button { background: #202839 }` — fix the token, delete the override.
- Success dot with no label: add "Active" text + maintain dot.
- `rgba(0,0,0,0.08)` literal → `var(--color-surface-hover)` or `$black-alpha-8`.
- `color: var(--color-text-tertiary)` on body paragraph → promote to `--color-text-secondary`.
- Warning text on page background at body size without icon/tinted bg — finding, fails contrast.
