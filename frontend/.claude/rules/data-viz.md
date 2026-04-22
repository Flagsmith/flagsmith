# Rule: data visualisation — charts and data-heavy tables (Flagsmith)

Chart and table specifics — axes, gridlines, legends, expandable rows, narrow-viewport behaviour. All colour tokens work in both light and dark mode.

Rules marked **[manual review]** cannot be auto-checked.

---

## 1. Chart anatomy

Every chart has: plot area, axes (0–2), gridlines (optional), series (≥1), legend (when ≥2 series), tooltip, annotations (optional).

### Spec

| Element | Token | Value |
|---|---|---|
| Plot area bg | `var(--color-surface-subtle)` | — |
| Plot area padding | 16px top/right, 32px bottom (axis space), 40px left (axis space) | |
| X-axis line | 1px `var(--color-border-strong)` | zero/baseline axis |
| Y-axis line | Usually absent — gridlines do the work | — |
| Axis tick labels | 12/16 400 `var(--color-text-secondary)` | |
| Axis title (when present) | 11/16 600 UPPERCASE `var(--color-text-secondary)` | |
| Major gridlines | 1px `var(--color-border-default)` (~16% alpha, flips per mode) | |
| Minor gridlines | 1px at ~4% alpha, dashed — use `$black-alpha-8` / `$white-alpha-8` via a mode-aware wrapper if a semantic token doesn't yet exist | |
| Zero/baseline | 1px `var(--color-border-strong)` | brighter, emphasised |

### Rules

1. **Gridline alpha flips per mode automatically** when using `var(--color-border-default)` / `--color-border-strong` — the token value is `slate-500 @ 16%` in light and `white @ 16%` in dark, so the same declaration reads correctly in both. Don't hand-write `rgba(255,255,255,...)` or `rgba(0,0,0,...)` in chart styles.
2. **No vertical gridlines unless X-axis is numeric** (time series, scatter). Categorical X-axes get no vertical gridlines — the bars provide vertical structure.
3. **Always show the zero baseline.** Bar charts treat the axis as baseline; line charts crossing zero render it distinctly. Omitting zero is misleading.
4. **Y-axis starts at zero for bar charts.** Non-zero baselines exaggerate differences. `major` `high`.
5. **Line charts can have non-zero baselines** when the data range warrants it, but label clearly.

### What the auditor checks

- Plot area bg resolves to `var(--color-surface-subtle)` (auto).
- Axis tick labels use 12/16 `--color-text-secondary` (auto).
- Zero baseline present and visually distinct (auto).
- Bar chart Y-axis min is 0 (auto).
- No vertical gridlines on categorical X-axes (auto).
- No hand-written `rgba(...)` for gridlines (auto).

---

## 2. Legend patterns

### Inline legend (preferred for ≤4 series)

```
[■ Series A]  [■ Series B]  [■ Series C]
```

Above the chart, left-aligned, 16px horizontal gap between items.

| Element | Token |
|---|---|
| Swatch | 10×10, `border-radius: var(--radius-xs)` (2px) |
| Label | 12/16 400 `var(--color-text-default)` |
| Swatch→label gap | 6px |
| Item gap | 16px |

### Table legend (for ≥5 series or when series have associated values)

Compact table below the chart: swatch | series name | latest value | change.

| Column | Token |
|---|---|
| Swatch column | 24px wide, 10×10 centred |
| Series | 13/18 400 `var(--color-text-default)` |
| Value | 13/18 500 `tabular-nums` `var(--color-text-default)` |
| Change | 13/18 500 `tabular-nums`, `var(--color-text-success)` or `--color-text-danger` with sign + arrow |

### Rules

1. **Legend order matches series order.**
2. **Legend items are clickable when ≥4 series** — click toggles visibility. Hidden: 0.4 opacity + strikethrough.
3. **Legend never wraps awkwardly.** If it would wrap to 3+ rows, switch to table legend.

### What the auditor checks

- Legend present when ≥2 series (auto).
- Swatch 10×10 with `--radius-xs` (auto).
- Legend item typography 12/16 (auto).
- **[manual review]** legend pattern choice matches series count.

---

## 3. Chart series colours

Flagsmith's 10-colour palette leads with **blue**, not purple. Brand purple is slot 5.

```
--color-chart-1   blue-500      (dark: blue-400)   ← default single-series
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

Because the default single-series colour is blue (chart-1) and the brand is purple (chart-5), series colour and selection highlight don't collide by default — the Obsidian-system worry about "primary-as-series vs primary-as-selection" doesn't apply to Flagsmith as long as both roles stick to their canonical tokens.

### Assignment rules

1. **Default single-series line/bar uses `--color-chart-1`** (blue). Exception: if the chart is about a specific status (success, failure, pending), use the semantic token.
2. **Categorical series use chart-1 → chart-10 in declaration order.** Don't resequence.
3. **Sequential data (gradient low→high)** uses a single-hue scale. Don't use a categorical palette for sequential data.
4. **Diverging data (correlation, variance from target)** uses `--color-chart-2` (red) → neutral mid → `--color-chart-1` (blue). **Never use white as midpoint** — disappears in light mode, punches through in dark. Use `--color-surface-muted` as the mid step.
5. **Never more than 6 colours in one chart.** Switch to small multiples for >6 series.
6. **Don't resequence the canonical palette** without a review — series order matters for memory across dashboards.

### What the auditor checks

- Single-series charts use `--color-chart-1` unless a semantic reason drives otherwise (auto).
- Series colours appear in declaration order from chart-1 (auto).
- No white midpoint on diverging scales (auto).
- ≤6 categorical colours per chart (auto).

---

## 4. Tooltip / crosshair

### Spec

| Element | Token |
|---|---|
| Tooltip bg | `var(--color-surface-subtle)` (or inverse tooltip bg — see `components.md`) |
| Tooltip border | 1px `var(--color-border-default)` |
| Tooltip radius | `var(--radius-sm)` |
| Tooltip shadow | `var(--shadow-md)` |
| Tooltip padding | 8×10 |
| Tooltip typography | 12/16 |
| Tooltip min-width | 140px |
| Crosshair | 1px dashed `var(--color-border-strong)` |
| Point highlight | 5px (3px default scaled up) |

### Tooltip content rules

1. **Category / X value** (date, label) — 12/16 weight 500 `var(--color-text-default)`.
2. **For each series**: swatch · series name · value.
   - Series name: 12/16 weight 400 `var(--color-text-secondary)`.
   - Value: 12/16 weight 500 `tabular-nums` `var(--color-text-default)`.
3. **Delta or comparison when relevant** — 11/16 `var(--color-text-secondary)`.

### Rules

1. Tooltips appear on crosshair hover, not point-by-point. Single tooltip shows all series at that X.
2. Tooltip position above-left or above-right of cursor, flipping below near top edge.
3. Crosshair persists while tooltip is shown.
4. `tabular-nums` on every value.

### What the auditor checks

- Tooltip uses 12/16 typography (auto).
- Tooltip values use `tabular-nums` (auto).
- **[manual review]** tooltip shows all series at a given X.

---

## 5. Tables with expandable rows

### Spec

| Element | Token |
|---|---|
| Chevron column | 32px wide, chevron 14px centred |
| Chevron default | `var(--color-icon-secondary)`, pointing right |
| Chevron expanded | rotated 90°, colour `var(--color-icon-default)` |
| Expanded content background | `var(--color-surface-muted)` — one step from row bg in both modes |
| Expanded content padding | 16px vertical, 16px horizontal + 32px left (align under chevron) |
| Expand/collapse transition | `var(--duration-normal)` `var(--easing-standard)` |

### Rules

1. **Chevron in its own leftmost column**, 32px wide, chevron 14px.
2. **Clicking anywhere on the row toggles expansion** — not just the chevron.
3. **Single-row expansion is the default; multi-row is a product choice.** Within a single table, pick one.
4. **Expanded content doesn't break row width.** Fills full table width minus chevron indent.
5. **Expanded content height bounded** — if >400px, scroll internally.
6. **Keyboard**: Enter/Space on the row toggles; arrow keys navigate between rows regardless of expansion.

### What the auditor checks

- Chevron column is 32px (auto).
- Chevron transitions with `var(--duration-normal)` `var(--easing-standard)` (auto).
- Expanded bg is `var(--color-surface-muted)` (auto).
- **[runtime]** row hit area covers the full row.
- **[runtime]** expansion doesn't push content below fold uncontrollably.

---

## 6. Tables on narrow viewports

Three strategies; pick per table:

### Strategy A — Horizontal scroll (default)

Desktop-sized table scrolling horizontally inside its container.

- Container `overflow-x: auto`.
- Sticky first column: `position: sticky; left: 0`.
- Scrollbar styled subtly — 4–8px thumb at `var(--color-border-default)`.
- Scroll shadow on right edge when content overflows.

**Use when:** all columns equally important.

### Strategy B — Collapse to card

Each row becomes a vertical card on narrow viewports.

- Card padding 16px, radius `var(--radius-lg)`.
- Entity name becomes card title (`$h5-font-size`).
- Each column becomes a label-value pair: label 11/16 UPPERCASE `var(--color-text-secondary)`, value 13/18 `var(--color-text-default)`.
- Cards stack with 12px gap.
- Triggered at viewport <768px (Bootstrap `md`).

**Use when:** rows are discrete entities users act on one at a time.

### Strategy C — Hide secondary columns

Default table; columns marked `data-priority="secondary"` hide below `lg` (992px in Bootstrap 5), `data-priority="tertiary"` hide below `md` (768px).

**Use when:** some columns are clearly more important than others.

### Rules

1. **Every table declares its narrow-viewport strategy** via `data-narrow="scroll|collapse|hide"`. Undeclared = finding.
2. **Strategy is consistent within a product area.**
3. **First-column stickiness** required for Strategy A when columns ≥5.

### What the auditor checks

- Table has `data-narrow` attribute (auto).
- Scroll tables have sticky first column when ≥5 columns (auto).
- **[runtime, multi-viewport]** at <768px, the declared strategy actually works.

---

## 7. Chart / KPI responsive behaviour

### KPI grid

```scss
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;  // 16px
}
```

Collapses 4-across → 2-across → 1-across automatically.

### Chart responsive

1. **Chart width is always 100% of container** — never fixed px.
2. **Chart height is fixed or has a min-height** — charts without height collapse on first render.
3. **Small viewport charts**: at <640px (Bootstrap `sm`), hide axis titles (keep tick labels), reduce tick density by half, rotate X-axis labels if they would overlap.
4. **Legend becomes a modal or expandable** on narrow viewports if inline legend would wrap to 3+ rows.

### What the auditor checks

- KPI grid uses `auto-fit` (auto).
- Charts have explicit `min-height` (auto).
- **[runtime, multi-viewport]** charts readable at mobile.

---

## 8. Data density inside charts

1. **One chart, one primary message.**
2. **Data-ink ratio.** Every pixel should represent data. Remove gridlines that don't help; remove decorative shadows; remove border-radius on bars >4px (distorts length perception).
3. **Labels over legends** where possible. Line chart with 3 series can label line-ends, eliminating the legend.
4. **Consistent scales across related charts.** Side-by-side bar charts of the same metric share Y scale.

### What the auditor checks

- **[manual review]** chart has one primary message.
- **[manual review]** no decorative shadows / gradients / unnecessary borders.
- Side-by-side related charts share Y scales (auto).

---

## Data-viz auditor walk

1. Tokens: axis labels, gridlines, series colours, tooltip, swatch sizing.
2. Zero baseline on bar charts; zero line visible on line charts crossing zero.
3. Legend match: series count vs. inline/table legend; order matches series.
4. Tooltip format: category, series with swatches, values in `tabular-nums`.
5. Chart palette: uses `--color-chart-1` onwards in order.
6. Expandable row structure (if present): dedicated chevron column, animated rotation, neutral expansion bg.
7. Narrow-viewport strategy declared and working.
8. Visual hierarchy and decoration — judgment.
