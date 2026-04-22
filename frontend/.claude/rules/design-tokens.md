# Rule: design tokens (Flagsmith)

**Always load this module.** Every other rule assumes you know the token map.

Flagsmith is **dual-mode** (light default). Dark mode is applied by `web/project/darkMode.ts` which puts `.dark` on `<body>` (CSS tokens scoped under `.dark { ... }` cascade to all descendants) and `data-bs-theme="dark"` on `<html>` (for Bootstrap 5 theming); state is persisted in `localStorage.dark_mode`. Every colour decision must survive both modes. CSS custom properties in `:root` are the light values; `.dark` overrides them. SCSS primitives are mode-agnostic anchors.

## The hierarchy (strict)

1. **Semantic CSS custom properties** — `var(--color-text-default)`, `var(--color-surface-default)`, `var(--color-border-default)`. **Always reach here first in product code.** Auto-switches light↔dark.
2. **SCSS semantic vars** — `$primary`, `$success`, `$danger`, `$warning`, `$info`, and the legacy `$text-icon-*` / `$bg-*` family. Acceptable in SCSS when a CSS var doesn't yet exist for the concept. Flag any new usage that duplicates a CSS var.
3. **Primitive tokens** — `$slate-*`, `$purple-*`, `$red-*`, `$green-*`, `$gold-*`, `$blue-*`, `$orange-*` (scale 0–1000). Referenced only by the token layer itself (`_tokens.scss`, `_variables.scss`). **Never in component code.**
4. **Raw values** — hex literals, px values off the scale, decimal alpha. **Forbidden.**

Source of truth: `frontend/common/theme/tokens.json` → generated into `frontend/web/styles/_tokens.scss` **and** `frontend/common/theme/tokens.ts` by `npm run generate:tokens`. Edit the JSON, regenerate — never hand-edit either generated file.

## Consuming tokens from TS / JSX

**Always import from `common/theme/tokens.ts` rather than writing raw `var(--color-*)` strings in JSX.** The module is auto-generated from `tokens.json` and gives you typed named exports with built-in fallback values.

```tsx
import {
  colorTextSecondary,
  colorIconSecondary,
  colorIconAction,
  colorBorderAction,
  radiusMd,
  durationFast,
  easingStandard,
} from 'common/theme/tokens'

// ✓ Correct
<p style={{ color: colorTextSecondary }}>Descriptor</p>
<Icon fill={colorIconSecondary} />

// ✗ Wrong — raw CSS var string, loses type safety and fallback
<p style={{ color: 'var(--color-text-secondary)' }}>Descriptor</p>
```

Each export resolves to `'var(--token-name, <fallback-hex>)'` — the fallback keeps styles sane if the CSS layer hasn't loaded. Groups like `radius`, `shadow`, `duration`, `easing` also have `Record<string, TokenEntry>` exports if you need to iterate.

**Do not use `className='text-secondary'`** for the secondary-text token. Bootstrap 5 owns `.text-secondary` and maps it to `$secondary` (gold in Flagsmith) — it will render yellow. Use the `colorTextSecondary` TS import via inline style, or a design-system utility class that sets `color: var(--color-text-secondary)` and does not collide with Bootstrap's namespace.

## Semantic surface tokens (CSS vars)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-surface-default` | `$slate-0` (white) | `$slate-950` (#101628) | **Page background** |
| `--color-surface-subtle` | `$slate-50` | `$slate-900` | Card / raised region on the page |
| `--color-surface-muted` | `$slate-100` | `$slate-850` | Recessed well, secondary panel |
| `--color-surface-emphasis` | `$slate-200` | `$slate-800` | Strongest neutral fill (selected cell, prominent inset) |
| `--color-surface-hover` | `slate-1000 @ 8%` | `slate-0 @ 8%` | Row / card hover tint |
| `--color-surface-active` | `slate-1000 @ 16%` | `slate-0 @ 16%` | Row / card pressed |
| `--color-surface-action` | `$purple-600` | `$purple-400` | Primary CTA fill |
| `--color-surface-action-hover` | `$purple-700` | `$purple-600` | Primary CTA hover |
| `--color-surface-action-active` | `$purple-800` | `$purple-700` | Primary CTA pressed |
| `--color-surface-action-subtle` | `purple-600 @ 8%` | `slate-0 @ 8%` | Selected row, brand-tinted background |
| `--color-surface-action-muted` | `purple-600 @ 16%` | `slate-0 @ 16%` | Stronger brand tint, pressed-on-selected |
| `--color-surface-danger` | `red-500 @ 8%` light fill | `oklch(red-500 L=0.18)` dark fill | Danger banner / inline alert bg |
| `--color-surface-warning` | `orange-500 @ 8%` | `oklch(orange-500 L=0.18)` | Warning banner bg |
| `--color-surface-success` | `green-500 @ 8%` | `oklch(green-500 L=0.18)` | Success banner bg |
| `--color-surface-info` | `blue-500 @ 8%` | `oklch(blue-500 L=0.18)` | Info banner bg |

**Rules:**

- Never use `#000`, `#fff`, `$slate-0`, or `$slate-1000` directly as a surface — use the semantic var so dark mode flips.
- Never stack raised-on-raised-on-raised. Two elevations maximum (`default` → `subtle` / `muted`).
- Elevation is surface-lightness + a 1px `--color-border-default` rim. Shadow is atmosphere (`--shadow-sm/md/lg/xl`), not structure.

## Semantic text tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-text-default` | `$slate-600` (#1a2634) | `$slate-0` (white) | **Default body, table cells** |
| `--color-text-secondary` | `$slate-500` | `$slate-300` | Labels, helper text, captions |
| `--color-text-tertiary` | `$slate-300` | `slate-0 @ 48%` | De-emphasised meta, axis ticks |
| `--color-text-disabled` | `$slate-300` | `slate-0 @ 32%` | Disabled controls |
| `--color-text-action` | `$purple-600` | `$purple-400` | Links, brand text, focus text |
| `--color-text-danger` | `$red-500` | `$red-500` | Error copy, delta-negative |
| `--color-text-warning` | `$orange-500` | `$orange-500` | Warning copy |
| `--color-text-success` | `$green-500` | `$green-500` | Success copy, delta-positive |
| `--color-text-info` | `$blue-500` | `$blue-500` | Informational copy |

**Contrast floor (WCAG AA):**

- `--color-text-default` on `--color-surface-default` passes 4.5:1 in both modes.
- `--color-text-secondary` on `--color-surface-default` passes 4.5:1 in both modes (tested; light: ~5.2:1, dark: ~6:1).
- `--color-text-tertiary` is below 4.5:1 in some combinations — **body text must never use tertiary**. Tertiary is for decorative meta only (axis ticks, timestamps in low-priority contexts).
- `--color-text-disabled` is below 3:1 by design — disabled is exempt from contrast per WCAG 1.4.3.

## Semantic border tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-border-default` | `slate-500 @ 16%` | `slate-0 @ 16%` | **Default rim — cards, inputs, buttons** |
| `--color-border-strong` | `slate-500 @ 24%` | `slate-0 @ 24%` | Input hover, strong dividers |
| `--color-border-disabled` | `slate-500 @ 8%` | `slate-0 @ 8%` | Disabled control border |
| `--color-border-action` | `$purple-600` | `$purple-400` | **Focus ring, selected row bar** |
| `--color-border-danger` | `$red-500` | `$red-500` | Invalid input, danger banner edge |
| `--color-border-warning` | `$orange-500` | `$orange-500` | Warning banner edge |
| `--color-border-success` | `$green-500` | `$green-500` | Success banner edge |
| `--color-border-info` | `$blue-500` | `$blue-500` | Info banner edge |

## Semantic icon tokens

Mirror the text tokens: `--color-icon-default`, `--color-icon-secondary`, `--color-icon-disabled`, `--color-icon-action`, `--color-icon-danger`, `--color-icon-warning`, `--color-icon-success`, `--color-icon-info`.

Rule: icon colour follows the concept it represents. A status icon uses its semantic token; a decorative icon uses `--color-icon-secondary`.

## Chart tokens

```
--color-chart-1   blue-500     (dark: blue-400)    ← default single-series
--color-chart-2   red-500
--color-chart-3   green-500
--color-chart-4   orange-500
--color-chart-5   purple-500
--color-chart-6   blue-600
--color-chart-7   red-600
--color-chart-8   green-600
--color-chart-9   orange-600
--color-chart-10  purple-600
```

Flagsmith's chart palette leads with **blue**, not brand purple. Brand purple is slot 5. Don't resequence without a review — series order matters for memory across dashboards.

## Radius

```
--radius-none  0
--radius-xs    2px
--radius-sm    4px    ← small chips, tight pills
--radius-md    6px    ← inputs, buttons, default controls
--radius-lg    8px    ← cards
--radius-xl    10px   ← modals (alternative)
--radius-2xl   18px   ← large featured surfaces
--radius-full  9999px ← pills, switches, circular avatars
```

**Rules:**

- Controls (buttons, inputs, selects) use `--radius-md` (6px).
- Cards and larger panels use `--radius-lg` (8px).
- Never exceed `--radius-2xl` (18px) in product chrome. Full-radius is for pills / avatars / switches only.
- Radius never scales with density.

## Shadow

```
--shadow-sm   subtle (resting raised surface)
--shadow-md   default (dropdowns, popovers)
--shadow-lg   modal, drawer
--shadow-xl   high-emphasis modal / full-screen takeover
```

Dark mode shadows are stronger (0.20–0.40 alpha vs 0.05–0.20 light) — the tokens already account for this. Don't write mode-specific shadow overrides in components.

## Motion

```
--duration-fast    100ms   hover, focus ring, press
--duration-normal  200ms   dropdowns, tooltips, tabs (default)
--duration-slow    300ms   modals, drawers, sheets

--easing-entrance  cubic-bezier(0.0, 0, 0.38, 0.9)
--easing-exit      cubic-bezier(0.2, 0, 1.0, 0.9)
--easing-standard  cubic-bezier(0.2, 0, 0.38, 0.9)
```

Everything over 300ms must earn it through real spatial movement. See `motion.md`.

## SCSS primitives (for token-layer authoring only)

Full scales live in `_primitives.scss`:

```
$slate-0 … $slate-1000    (0 is white, 1000 is black, 13 steps)
$purple-50 … $purple-950   (brand — 10 steps, generated from purple-600 anchor)
$red-50 … $red-950         (danger)
$green-50 … $green-950     (success)
$gold-50 … $gold-950       (secondary)
$blue-50 … $blue-950       (info)
$orange-50 … $orange-950   (warning)
```

These exist so the token layer can interpolate and build dark-mode variants. **Never use them in a component.** If you find `color: $slate-600` in a component, it's a finding.

## SCSS legacy semantic vars (`_variables.scss`)

Retained for Bootstrap overrides and files that haven't been migrated to CSS vars yet:

- `$primary`, `$primary400`, `$primary600`, `$primary700`, `$primary800`, `$primary900`
- `$success`, `$success400`, `$success600`, `$danger`, `$danger400`, `$info`, `$warning`
- `$body-bg-dark`, `$body-color`, `$body-color-dark`, `$text-icon-light`, `$text-icon-grey`
- `$header-color`, `$header-color-dark`

**Rules:**

- New code should prefer CSS custom properties (`var(--color-*)`) over SCSS semantic vars.
- When editing a file that already uses SCSS vars, staying consistent is fine — don't mix both in one file.
- `$body-color` / `$body-color-dark` are mode-specific by name; prefer `--color-text-default` which swaps automatically.

## The three workhorses (memorise)

- **Colour**: `--color-text-default`, `--color-surface-default`, `--color-border-default`.
- **Radius**: `--radius-md` (controls), `--radius-lg` (cards).
- **Motion**: `--duration-fast` (hover), `--duration-normal` (default), `--easing-standard`.

If you reach for one of these, you're probably right. If you reach past them, you need a reason.

## Spacing note

Flagsmith does not yet have a semantic spacing token layer (no `--space-*` vars, no `$space-inset-*` aliases). Spacing is Bootstrap-derived: `$spacer` (16px) and multipliers. See `spacing.md` for the canonical scale and anti-patterns.

## Typography note

Flagsmith does not yet have semantic typography tokens like `$font-body` / `$font-heading-m`. It has raw size vars (`$h1-font-size` … `$h6-font-size`, `$font-size-base`, `$font-caption`, `$font-caption-sm`, `$font-caption-xs`) and legacy Bootstrap `$font-weight-*` maps. See `typography.md` for which vars to use where.

## Forbidden patterns (automatic findings)

- Hex literals in component files: `color: #1a2634` → `color: var(--color-text-default)`.
- Primitive SCSS vars in components: `color: $slate-600` → `color: var(--color-text-default)`.
- Pure `#000` / `#fff` as surface or body text.
- `color: white` on body text in a dual-mode file (it won't flip for light mode).
- Decimal alpha literals: `rgba(255,255,255,0.08)` → `var(--color-surface-hover)` or the named `$white-alpha-8`.
- Pixel values for radius: `border-radius: 6px` → `var(--radius-md)`.
- Raw durations: `transition: 200ms` → `var(--duration-normal)`.
- Raw easing strings: `cubic-bezier(...)` → `var(--easing-standard)`.
- Mode-specific colours written inline in a component via `.dark` selectors — if the CSS var doesn't flip correctly, fix the token, don't override the component.
- Arbitrary z-index values — use Bootstrap's `$zindex-*` map (`$zindex-dropdown`, `$zindex-modal`, etc.).

## When no token fits

**Stop.** Do not invent a value. Either:

1. The design is violating the system and must change; or
2. There is a missing token — add it to `common/theme/tokens.json`, regenerate, then use it.

Flag with `// fs-audit: missing-token — <context>` and escalate.
