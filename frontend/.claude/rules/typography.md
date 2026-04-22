# Rule: typography (Flagsmith)

OpenSans, 14px base (`0.875rem`), three usable weights, Bootstrap-derived heading scale.

Flagsmith does NOT yet have semantic type tokens (`$font-body`, `$font-heading-m`, etc.). Until those exist, use the raw size / line-height vars below. **Do not invent new sizes**; pick from the scale.

## Family

- `$font-family-base: 'OpenSans', sans-serif` — applied at `<body>`.
- No established mono family — inline `<code>` inherits browser default monospace. If adding code blocks, use `font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` and propose a new SCSS var.

## The scale (raw vars → role)

| Role | SCSS vars | px | Weight | Use |
|---|---|---|---|---|
| Display (h1) | `$h1-font-size` / `$h1-line-height` | 42 / 46 | 700 | Marketing / hero only — not in app chrome |
| Page title (h2) | `$h2-font-size` / `$h2-line-height` | 34 / 40 | 600 | Top-level page title |
| Section (h3) | `$h3-font-size` / `$h3-line-height` | 30 / 40 | 600 | Prominent section heading |
| Sub-section (h4) | `$h4-font-size` / `$h4-line-height` | 24 / 32 | 600 | **Typical page section heading inside app** |
| Card title (h5) | `$h5-font-size` / `$h5-line-height` | 18 / 28 | 600 | **Card / panel title** |
| Small heading (h6) | `$h6-font-size` / `$h6-line-height` | 16 / 24 | 600 | Dense group heading |
| Body base | `$font-size-base` / `$line-height-base` | 14 / ~19.25 | 400 | **Default body, inputs, menu items** |
| Body (`font-sm`) | `$font-sm` / `$line-height-sm` | 14 / 20 | 400 | Same size as base, 20px line where grid matters |
| Caption | `$font-caption` / `$line-height-xsm` | 13 / 18 | 400 | Table cell, sidebar item, helper text |
| Caption small | `$font-caption-sm` / `$line-height-xxsm` | 12 / 16 | 400 | Axis labels, tags, tight meta |
| Caption xs | `$font-caption-xs` / `$line-height-xxsm` | 11 / 16 | 500 | Overline / badge / tiny labels |

Line heights live on the 4-grid (16 / 18 / 20 / 24 / 28 / 32 / 40 / 46) — any value off this grid is a finding.

## Tag → role mapping

- `<h1>` — page title (one per page). If the page uses `<h2>` for the title (legacy pattern in some pages), don't add a second `<h1>` just to satisfy this rule; fix the tag.
- `<h2>` — section heading.
- `<h3>` — sub-section.
- `<h4>` — group heading inside a section / card title alternative.
- `<h5>` — card title.
- `<h6>` — dense group heading inside a card.
- `<p>` — default body.
- `<label>` — form field label; `$font-size-base` weight 500 (`--input-label-weight` if introduced).
- `<small>` / `.helper-text` — `$font-caption`.
- `<code>` / `<kbd>` — mono stack, inherit body size.

**Never** style a `<div>` / `<span>` as a heading to get the visual weight. Use the right tag. Screen readers and the outline auditor will both flag it.

## Weights

Only three weights in product code:

- **400 (regular)** — body, table cells, menu items, input values, inactive tabs.
- **500 (medium)** — form labels, button labels, tab labels, deltas, active nav items. Bootstrap's `$font-weight-medium`.
- **600 (semibold)** — headings (h2–h6), KPI values, primary button labels in some variants. Bootstrap's `$font-weight-semibold`.

**Forbidden:**

- Weight 300 below 24px — OpenSans Light goes stringy.
- Weight 800 in app chrome at all.
- Weight 700 as a standalone heading weight — use 600. (700 is permitted for `<strong>` inline emphasis; `$btn-font-weight` also defaults to 700 in the current buttons — that's a known legacy and the buttons file stays as-is until a broader button pass.)

## Tabular numerals

Apply `font-variant-numeric: tabular-nums lining-nums` wherever numbers sit in columns or need to align across rows:

```scss
.tabular,
table td,
table th,
.kpi-value,
time,
code,
.timestamp,
.metric,
[data-numeric] {
  font-variant-numeric: tabular-nums lining-nums;
}
```

**Never** on prose or headings — proportional digits read more refined inline; tabular digits create awkward gaps.

Missing `tabular-nums` on a numeric table column is an auto finding.

## Text colours (see color.md for full palette)

- Headings: `var(--color-text-default)` by default. Dual-mode safe.
- Body: `var(--color-text-default)`.
- Secondary / helper: `var(--color-text-secondary)`.
- Tertiary / meta: `var(--color-text-tertiary)` — never on body text.

**Don't** set `color: $header-color` / `$header-color-dark` in a component — those are for the token layer. Let headings inherit or set `var(--color-text-default)`.

## Measure

- Body prose containers: `max-width: 65ch`.
- Tables and KPI cards: no max-width.
- Modal body, empty state, help text, settings descriptions: `max-width: 65ch`.

Fixed pixel widths on text containers are forbidden — they break 200% zoom.

## Common violations

- `font-size: 15px` — not on scale. Pick 14 (`$font-size-base` / `$font-sm`) or 16 (`$h6-font-size`).
- `font-size: 17px`, `font-size: 22px`, any off-scale px value → pick the nearest scale value.
- `font-weight: 700` on a heading → use 600.
- `font-weight: 500` as a raw literal → use `$font-weight-medium` in SCSS.
- `line-height: 1.5` on 14px body → should be 20px (ratio ~1.43) not 21px.
- `font-family: 'Inter'` / any non-OpenSans family in app chrome.
- Missing `tabular-nums` on numeric columns.
- Negative letter-spacing on body text <16px — reserved for large headings if ever.
- `color: white` on a heading in a dual-mode component — use `var(--color-text-default)`.
