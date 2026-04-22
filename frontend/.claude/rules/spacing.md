# Rule: spacing (Flagsmith)

Bootstrap 5 scale: `$spacer` = 16px, five steps. Three workhorses — 16, 24, 32 — cover most decisions.

## The scale

```scss
$spacer: 1rem;  // 16px

// Bootstrap 5 spacing map (already wired):
// 0 → 0
// 1 → $spacer * 0.25    = 4px
// 2 → $spacer * 0.5     = 8px
// 3 → $spacer           = 16px
// 4 → $spacer * 1.5     = 24px
// 5 → $spacer * 2       = 32px
```

Half-step (`0.25rem = 4px`) is the smallest layout gap. No `2px` layout values — 2px is reserved for focus ring offsets and hairlines.

Custom utility: `px-12` = 6rem = 96px (marketing pages only; not for app chrome).

## Utility classes

Use Bootstrap's utility classes for spacing in TSX / JSX markup — it's the house style:

- `m-{0-5}` / `p-{0-5}` — all-sides margin / padding.
- `mt/mb/ms/me/mx/my-{0-5}` — sided margin.
- `pt/pb/ps/pe/px/py-{0-5}` — sided padding.
- Legacy `ml-*/mr-*/pl-*/pr-*` still compile via `_spacing-utils.scss` but BS5 renamed these to `ms-*/me-*/ps-*/pe-*` — prefer the new form in new code.
- `gap-{0-5}` — flex / grid gap.
- `row-gap-{2,4}` — custom helpers for explicit row gap.

**Rule.** Prefer `gap` utilities (`gap-2`, `gap-3`) over stacking `me-*` / `mb-*` on each child. Margins-between-siblings is a 2010 pattern; `gap` is the 2024 pattern.

## Semantic mapping (recommended usage)

Flagsmith has no `$space-inset-*` / `$space-stack-*` aliases yet. Until it does, use the numeric scale, but mentally map it:

| Intent | Class / value | px |
|---|---|---|
| Icon ↔ text, checkbox ↔ label | `gap-1` | 4 |
| Chip gap, button icon gap | `gap-2` | 8 |
| Default inline gap | `gap-2` | 8 |
| Label → value, tight stack | `mt-1` / `gap-1` | 4 |
| Small list item stack | `gap-2` | 8 |
| Form-field stack | `gap-3` | 16 |
| Card contents stack | `gap-3` | 16 |
| Compact card padding | `p-3` | 16 |
| Default card padding | `p-3` or `p-4` | 16–24 |
| Comfortable card padding | `p-4` | 24 |
| **Section → section** (default) | `gap-4` / `mb-4` | 24 |
| Section → section (comfortable) | `gap-5` / `mb-5` | 32 |
| Dashboard grid gap | `gap-3` | 16 |
| Page horizontal padding | `px-4` | 24 |

**Default "don't-think" choices:**

- Card padding: `p-3` (16px).
- Form fields stack: `gap-3` (16px).
- Section gap: `mb-4` (24px).
- Page horizontal padding: 24px (via `px-4` or the page shell).

## Rules (strict)

1. **Use `gap`, not `margin`, on siblings** whenever the parent is flex or grid. Margin is for overrides.
2. **Proximity ratio 1 : 2–3 : 4–6.** Within-group : between-group : section-to-section. (Example: 4px label-value, 12–16px between fields, 24px between sections.)
3. **Start from more, trim down.** When uncertain between `mb-3` (16) and `mb-4` (24) — pick `mb-4`. A generous boundary that looks clear is better than a cramped one that reads as one block.
4. **Page horizontal padding is consistent at every breakpoint inside app chrome** — whatever the shell chooses (typically 16–24), don't vary it per-page.
5. **Card contents gap is 16px** (`gap-3`). Form-field gap is 16px (`gap-3`). Section gap is 24px (`mb-4`).
6. **Heading → descriptor → content spacing**: 4–6px heading→descriptor (tight — one unit), 12–16px descriptor→content (clear break). See `composition.md`.

## Common violations

- `padding: 13px` / `margin: 15px` — not on scale. Pick 12 (`p-3`-adjacent) or 16 (`p-3`). If neither fits, the scale is right and the design is wrong.
- `padding: 20px` — not a Bootstrap step. Pick 16 (`p-3`) or 24 (`p-4`). 20 is valid in Obsidian but not in this system.
- `margin-bottom: 10px` — pick 8 (`mb-2`) or 16 (`mb-3`).
- `margin-right: 8px` on every sibling in a flex row → replace with `gap-2` on the parent.
- `margin: 10px 15px` — arbitrary composite. Break into inset utility classes.
- Inconsistent spacing between similar elements (16 here, 20 there for the same card pattern).
- Section headings with 30–40px below them — should be 12–16px heading→content, 24–32px section→section.
- `padding: 2rem` / `margin: 3rem` — use `p-5` / `m-5` utilities for readability.
- Hand-written `margin-top: 4px` when `mt-1` exists — drift; use the utility.

## When the scale doesn't fit

**Stop.** Three options:

1. Rework the design to the scale.
2. Propose a scale extension (rare — the existing scale covers 95% of dashboards).
3. Use an explicit `$spacer * N` calculation in SCSS with a comment explaining why. Never use a raw off-grid px value.
