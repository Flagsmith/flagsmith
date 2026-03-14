---
title: "Define formal colour primitive palette"
labels: ["design-system", "large-refactor", "tokens"]
status: DRAFT
---

## Problem

The codebase has no systematic colour palette. Greys are defined ad hoc in
`_variables.scss` and hardcoded directly in components. There is no `$neutral-*`
or `$purple-*` scale that other tokens can reference.

### Specific issues

1. **Ad hoc grey definitions** — `_variables.scss` defines greys as one-off
   variables with no scale relationship:
   - `$text-icon-grey: #656d7b`
   - `$text-icon-light-grey: rgba(157, 164, 174, 1)` (equivalent to `#9DA4AE`)
   - `$body-color: #1a2634`
   - `$header-color: #1e0d26`
   - `$bg-dark500: #101628` through `$bg-dark100: #2d3443`

2. **Highest-frequency hardcoded values** — these hex values appear dozens of
   times across the codebase with no token:
   - `#9DA4AE` — 59 occurrences across 35 files (light grey text/icons)
   - `#656D7B` — 75 occurrences across 48 files (secondary text)
   - `#1A2634` — used as body colour and icon default fill

3. **Brand purple has no scale** — `_variables.scss` defines:
   - `$primary: #6837fc`
   - `$primary400: #906af6`
   - `$primary600: #4e25db`
   - `$primary700: #3919b7`
   - `$primary800: #2a2054`
   - `$primary900: #1E0D26`

   But these don't follow a consistent naming convention and `$primary900`
   (`#1E0D26`) is actually a near-black, not a dark purple — it's the same
   value as `$header-color`.

4. **`_primitives.scss` exists but is incomplete** — the file was drafted with
   `$slate-*` and `$purple-*` scales that `_tokens.scss` already references, but
   the primitives are not yet used to replace ad hoc values in `_variables.scss`
   or in component code.

5. **Background dark scale is informal** — `$bg-dark500` through `$bg-dark100`
   use a loose numbering system that doesn't align with the standard
   50/100/200/.../950 convention.

## Files

- `web/styles/_variables.scss` — current ad hoc colour definitions (~60 lines of
  colour variables)
- `web/styles/_primitives.scss` — drafted primitive palette (incomplete)
- `web/styles/_tokens.scss` — semantic tokens that reference primitives

## Proposed Fix

### Step 1 — Define the neutral (slate) scale

Create a complete `$slate-*` scale in `_primitives.scss`:

```scss
// Neutral / Slate
$slate-0:    #ffffff;
$slate-50:   #fafafb;
$slate-100:  #eff1f4;
$slate-200:  #e0e3e9;
$slate-300:  #9da4ae;   // maps to existing #9DA4AE (59 uses)
$slate-400:  #8a919b;
$slate-500:  #656d7b;   // maps to existing #656D7B (75 uses)
$slate-600:  #1a2634;   // maps to existing $body-color
$slate-800:  #2d3443;   // maps to existing $bg-dark100
$slate-850:  #202839;   // maps to existing $bg-dark200
$slate-900:  #15192b;   // maps to existing $bg-dark400
$slate-950:  #101628;   // maps to existing $bg-dark500
```

(Exact values to be confirmed by visual comparison; the above maps known hex
values to the nearest scale step.)

### Step 2 — Define the purple (brand) scale

```scss
// Brand / Purple
$purple-400: #906af6;   // maps to existing $primary400
$purple-600: #6837fc;   // maps to existing $primary
$purple-700: #4e25db;   // maps to existing $primary600
$purple-800: #3919b7;   // maps to existing $primary700
```

Remove the misleading `$primary900: #1E0D26` (it's a neutral, not a purple).

### Step 3 — Define feedback scales

```scss
// Feedback
$red-500:    #ef4d56;   // maps to existing $danger
$red-400:    #f57c78;   // maps to existing $danger400
$green-500:  #27ab95;   // maps to existing $success
$green-400:  #56ccad;   // maps to existing $success400
$green-600:  #13787b;   // maps to existing $success600
$orange-500: #ff9f43;   // maps to existing $warning
$blue-500:   #0aaddf;   // maps to existing $info
```

### Step 4 — Map existing variables to primitives

Update `_variables.scss` to reference primitives instead of hardcoded hex:

```scss
// Before
$body-color: #1a2634;
$text-icon-grey: #656d7b;

// After
$body-color: $slate-600;
$text-icon-grey: $slate-500;
```

### Step 5 — Document the mapping

Add a comment block at the top of `_primitives.scss` listing every old hex value
and its new primitive equivalent, so reviewers can verify the mapping is correct.

## Acceptance Criteria

- [ ] `_primitives.scss` defines complete `$slate-0` through `$slate-950` scale
- [ ] `_primitives.scss` defines `$purple-*` scale for brand colours
- [ ] `_primitives.scss` defines `$red-*`, `$green-*`, `$orange-*`, `$blue-*`
      for feedback colours
- [ ] `_variables.scss` references primitives instead of hardcoded hex values
- [ ] `$primary900: #1E0D26` is removed or remapped to a neutral
- [ ] `_tokens.scss` compiles without errors using the new primitive references
- [ ] `npm run build` passes with no visual changes in light or dark mode
- [ ] Mapping documentation exists in `_primitives.scss` comments

## Dependencies

- This is a **prerequisite for LR-2** (Semantic colour tokens) — the semantic
  layer references primitives
- Enables **LR-7** (Full dark mode pass) — primitives make it straightforward to
  define dark overrides
- No blocking dependencies — this can start immediately

---
Part of the Design System Audit (#6606)
