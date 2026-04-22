# Rule: composition patterns (Flagsmith)

The other rule files describe **parts** (buttons, inputs, cards). This file describes **wholes** — the recurring structural units pages are built from. Most real bugs live here: a button at the wrong size next to a heading at the wrong size inside a section with no descriptor.

Every pattern is evaluable by the auditor. Where a rule requires judgment, it says so and provides concrete proxies. Findings that depend on judgment carry explicit confidence (`high` / `medium` / `low`). Rules marked **[manual review]** cannot be auto-checked.

---

## 1. Heading + descriptor + content (the workhorse)

A heading introduces a region; a descriptor explains it in plain English; content follows. Three-quarters of the product uses this pattern.

### Anatomy

```
[heading]                           ← required
[descriptor]                        ← required unless all three exceptions met
[content]                           ← required — table, chart, card grid, form
```

### Spec

| Slot | Element | Token | Colour | Gap to next |
|---|---|---|---|---|
| Heading | `<h2>` (section) or `<h5>` (card) | `$h2-font-size` (34/40) or `$h5-font-size` (18/28) | `var(--color-text-default)` | 4px (`mt-1` below) |
| Descriptor | `<p>` | `$font-caption` (13/18) | `var(--color-text-secondary)` | 12–16px |
| Content | — | — | — | — |

The **heading→descriptor gap is 4px** — they're one visual unit. The **descriptor→content gap is 12–16px** — the break between "what this is" and "the thing itself".

**Pick within the range by what sits below:**

| Content below descriptor | Gap | Why |
|---|---|---|
| Card with its own padding and rim border | 12px | Card's border provides the visual break |
| Form with a clear first field | 12px | Field border provides break |
| Table (whose `<thead>` is small subtle) | 16px | Table top is visually soft |
| Chart (no top boundary on itself) | 16px | No visual top boundary |
| Prose / paragraph | 16px | Text blends with text; needs room |

**Default when uncertain: 16px (`mb-3`).** Going wider is safer than tighter.

### Size-ratio rule (auto-checkable)

The heading must clearly out-rank the descriptor. 1.3× is the comfort floor.

| Heading | Minimum descriptor size |
|---|---|
| `$h2-font-size` (34) | `$h6-font-size` (16) or smaller |
| `$h3-font-size` (30) | `$font-size-base` (14) or smaller |
| `$h4-font-size` (24) | `$font-caption` (13) or smaller |
| `$h5-font-size` (18) | `$font-caption-sm` (12) or smaller |
| `$h6-font-size` (16) | **no descriptor permitted** — too close to body |

**Auditor check**: compute `heading.fontSize / descriptor.fontSize`. If <1.2 → `major` `high`. If 1.2–1.29 → `minor` `medium` with "bump heading up one step or shrink descriptor."

### When the descriptor may be omitted

Descriptor is omitted only when **all three** hold:

1. Heading is a generic label users understand (`Activity`, `Filters`, `Notes`, `Recent`, `History`, `Details`, `Overview`).
2. Content immediately demonstrates what it is (a table with clear column headers; a labelled form).
3. Removing the descriptor shortens the page without losing information.

**Auditor proxy**: a descriptor-less heading is clean if (a) heading text is ≤2 words AND matches the generic-label list AND (b) the next sibling is a `<table>` with `<thead>` or a `<form>`. Flag `minor` `medium` otherwise.

### Descriptor quality rule (proxy-checkable)

The descriptor must explain the heading to a new user. Not marketing copy, not a tagline, not a command.

- Good: "How your flags have rolled out across the last 30 days of traffic, across 142 environments."
- Bad: "Stay on top of your feature flags." (marketing fluff)
- Bad: "Flag rollouts by day." (restates heading)
- Bad: "View trends, compare periods, export to CSV." (describes controls)

**Auditor proxies:**

- Descriptor contains at least one of: a number, a content-type noun (`flag`, `environment`, `segment`, `identity`, `feature`, etc.), or a named entity.
- Descriptor is not a near-restatement of the heading (token overlap ≥ 60% with stop-words removed).
- Descriptor does not begin with a marketing verb (`Stay`, `Unlock`, `Get`, `Supercharge`).
- Descriptor does not begin with a UI-control verb (`View`, `See`, `Click`, `Tap`, `Hover`).

One proxy failing = `minor` `medium`. Two or more = `major` `medium`.

### States

The heading / descriptor persist through every content state — it is the frame, not the contents.

- **Loading**: heading + descriptor render normally; content area shows skeleton.
- **Empty**: heading + descriptor render normally; content area shows empty state.
- **Error**: heading + descriptor render normally; content area shows error state.

### What the auditor checks

- Heading tag is directly followed by `<p>` descriptor in a common parent (auto).
- Heading→descriptor gap ≤6px; descriptor→content gap 12–16px (auto).
- Descriptor colour resolves to `var(--color-text-secondary)` (auto).
- Heading tag matches role: `<h2>` for section, `<h5>` for card (auto).
- Size ratio per the table above (auto).
- Descriptor present, or all three exception conditions met (proxy-based).
- Descriptor-quality proxies (auto).

---

## 2. Page title row

Top of every main page. A title identifies the page; optional metadata sits beside it; optional actions sit at the far right.

### Anatomy

```
[title]   [metadata chips]                        [actions]
         ↑ optional                                ↑ optional
```

One row, vertically centred, title flush-left, actions flush-right.

### Spec

| Slot | Element | Token | Colour |
|---|---|---|---|
| Title | `<h1>` — but the Flagsmith convention in most pages is `<h2>` for the page title (see `AdminDashboardPage.tsx`). New pages should use `<h1>` with `$h2-font-size` typography; existing pages keep `<h2>`. | `$h2-font-size` (34/40 600) | `var(--color-text-default)` |
| Metadata chip | `<span class="chip">` | `$font-caption-xs` (11/16 500) | per chip type |
| Actions | `<button>` | 32px (`xsm`) — action buttons in title row are smaller than default 44px | per variant |

```scss
.page-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;              // 8px title to first chip
  min-height: 40px;
  margin-bottom: 1.5rem;    // 24px before first section
}
.page-title-row .chips { display: flex; gap: 0.375rem; }   // 6px
.page-title-row .actions { margin-left: auto; gap: 0.5rem; }
```

### Chip types (informational)

| Type | Background | Border | Text |
|---|---|---|---|
| Date range | transparent | 1px `var(--color-border-default)` | `var(--color-text-secondary)` |
| Status (live) | `var(--color-surface-success)` | 1px `var(--color-border-success)` | `var(--color-text-success)` |
| Status (paused) | `var(--color-surface-muted)` | 1px `var(--color-border-default)` | `var(--color-text-secondary)` |
| Status (error) | `var(--color-surface-danger)` | 1px `var(--color-border-danger)` | `var(--color-text-danger)` |
| Count / volume | `var(--color-surface-muted)` | none | `var(--color-text-secondary)` |

Chips in this row are **informational only, never interactive**. If it needs to be editable, use a button.

### Rules

1. **One page title per page.** `<h1>` if possible; consistent heading tag at minimum.
2. **Title never truncates.** If it overflows at narrow viewports, wrap to two lines.
3. **More than three actions collapse to an overflow menu.** Never wrap action buttons.
4. **The descriptor is not in this row.** Descriptor goes below the row using pattern 1.

### What the auditor checks

- Exactly one page-title-row element at the top of the page (auto, high).
- Title container is flex with `align-items: center` (auto).
- Metadata chips use caption typography (auto).
- Chip colour matches its semantic class — a chip labelled "Live" resolves to `--color-text-success` (auto).
- Overflow menu exists when >3 actions (auto).
- **[manual review]** action priority order — primary rightmost.

---

## 3. Section (as a structural unit)

A section is a discrete region introduced by pattern 1 and separated from neighbours by whitespace. Most pages are a page title row + 2–6 sections.

### Spec

| Slot | Value |
|---|---|
| Section→section vertical gap | 24px (`mb-4`) default, 32px (`mb-5`) comfortable |
| Heading block → content gap | 12–16px (inside the block, handled by pattern 1) |
| Between content cards | 16px (`gap-3`) |
| Between content rows | 12px |

### Structural rules

1. **A section has one heading**, always at the top, using pattern 1.
2. **Sections do not nest.** A section does not contain another section with its own `<h2>`. If a region inside a section needs a heading, it's a card with an `<h5>` title.
3. **Cards do not nest inside cards.** Same `--color-surface-subtle` bg + 1px rim + radius as an ancestor is a finding.
4. **Sections do not have their own background.** Section sits on `--color-surface-default`; content inside gets `--color-surface-subtle`. Never fill the section itself.
5. **Sections do not have borders.** Separation is whitespace — the 24px gap is the divider.
6. **Side-by-side content within a section is permitted.** Two sections side-by-side is a grid layout, not sections.

### What the auditor checks

- Each section starts with an `<h2>` (auto).
- No `<h2>` descendant of another `<h2>`'s section container (auto).
- No card element (surface-subtle + rim) is a descendant of another such card (auto).
- Section container has no `background-color` set (auto).
- Section container has no non-zero `border-width` (auto).
- Section→section gap resolves to 24 or 32px (auto).
- Card-to-card gap within a section is 16px (auto).

---

## 4. Status row (colour dot + label + timestamp)

Small horizontal unit showing the state of something.

### Spec

| Slot | Element | Token | Colour |
|---|---|---|---|
| Dot | `<span class="dot">` | 6×6 circle, `border-radius: var(--radius-full)` | semantic fill |
| Label | `<span>` | 13/18 weight 500 | `var(--color-text-default)` |
| Timestamp | `<time>` | 11/16 weight 400 | `var(--color-text-secondary)` |

```scss
.status-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.status-row .dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}
```

### Dot colour by status

| Status | Dot | Label |
|---|---|---|
| Active / live / complete | `var(--color-text-success)` | `var(--color-text-default)` |
| Warning / degraded | `var(--color-text-warning)` | `var(--color-text-default)` |
| Error / failed | `var(--color-text-danger)` | `var(--color-text-default)` |
| Paused / inactive | `var(--color-text-secondary)` | `var(--color-text-default)` |
| Unknown / loading | `var(--color-text-secondary)` with pulse | `var(--color-text-secondary)` |

### Rules

1. **Dot is always paired with a label.** Never dot-alone — fails WCAG 1.4.1.
2. **Timestamp is optional** but always last when present.
3. **The separator is not a dot character.** Use a space. `·` is permitted only between label and timestamp when the row wraps.
4. **Timestamp uses relative time** ("2m ago") with absolute time on hover via `title`.

### What the auditor checks

- Dot element is 6×6 with `var(--radius-full)` (auto).
- Dot colour matches its semantic role (auto).
- Label follows the dot (auto).
- Timestamp is `<time>` with a `datetime` attribute (auto).
- Timestamp has a `title` attribute for absolute time (auto).
- No middle-dot character separator between dot/label (auto).

---

## 5. Page templates (canonical layouts)

### Template A — Analytics / dashboard page

```
[page title row]
[KPI grid: 4 tiles]                  ← self-labelling, no section heading
[Section B heading + descriptor]
[primary chart]
[Section C heading + descriptor]
[data table]
```

- KPI grid: `auto-fit minmax(240px, 1fr)`.
- Primary chart full-width, 320–400px tall.
- Table default density (40px rows in Flagsmith).
- Section gap: 24px.

### Template B — Form / settings page

```
[page title row]
[Section: Profile]
[form fields]
[Section: Preferences]
[form fields]
[Section: Danger zone]
[destructive actions]
```

- Content `max-width: 720px`.
- Form fields vertical, 16px gap (`gap-3`).
- Each section's content is a form, not a card.
- Destructive actions in their own section with a `var(--color-border-danger)` left accent.

### Template C — Detail / entity page

```
[page title row: entity name + status chip + actions]
[Summary strip: 4-6 key facts]
[Section: Overview]
[Section: Related items (table)]
[Section: Activity]
```

- Summary strip: label-value pairs, not KPI tiles.
- Label: 11/16 UPPERCASE `var(--color-text-secondary)`.
- Value: 14/20 `var(--color-text-default)`.

### What the auditor checks

- Page starts with a page title row (auto).
- Settings pages cap content at 720px width (auto).
- **[manual review]** page matches a template.
- **[manual review]** section order respected within a template.

---

## 6. HTML-tag-to-token mapping

| Tag | Role | Token |
|---|---|---|
| `<h1>` | Page title (new pages) | `$h2-font-size` (34/40) |
| `<h2>` | Page title (legacy) / section heading | `$h2-font-size` / `$h4-font-size` |
| `<h3>` | Prominent sub-section | `$h3-font-size` (30) |
| `<h4>` | Section / group heading | `$h4-font-size` (24) |
| `<h5>` | Card title | `$h5-font-size` (18) |
| `<h6>` | Dense group heading | `$h6-font-size` (16) |
| `<p>` | Body paragraph, descriptor | `$font-size-base` (14) or `$font-caption` (13) |
| `<p class="lead">` | Modal intro, onboarding | `$h6-font-size` (16) |
| `<label>` | Form field label | 14 weight 500 |
| `<small>` | Helper / caption | `$font-caption` |
| `<code>` / `<kbd>` | Inline code | monospace |

**Rule.** The tag carries semantic meaning (screen readers, outline). The token carries visual meaning. They must be consistent.

- **Never** style an `<h2>` as body text just to get a landmark — use `<h2>` with `.visually-hidden` instead.
- **Never** style a `<div>` / `<span>` as a heading — use the right heading tag.

### What the auditor checks

- Tag matches role — compare computed `font-size`/`font-weight` against expected token (auto).
- No `<div>` / `<span>` with `font-size ≥ 16px AND font-weight ≥ 600` standing alone (heading impersonation — auto, `medium`).
- Document outline sensible — no heading levels skipped (auto, `medium`).

---

## Composition auditor walk

1. Page has a page title row? (pattern 2)
2. Which template does it match? (pattern 5)
3. For each section below the title row, does it use heading+descriptor+content? (pattern 1)
4. Sections structurally correct — no nested `<h2>`, no section backgrounds, no card-in-card? (pattern 3)
5. Status rows well-formed? (pattern 4)
6. Headings use the right tag for their role, consistent with §6?

Finding confidence:

- **High**: structural (two page titles, nested sections, descriptor not using `--color-text-secondary`).
- **Medium**: ratio and proxy-based judgments.
- **Low**: [manual review] items.
