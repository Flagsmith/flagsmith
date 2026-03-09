---
title: "Refactor Icon.tsx: extract inline SVGs, retire IonIcon"
labels: ["design-system", "large-refactor"]
status: DRAFT
---

## Problem

`web/components/Icon.tsx` contains ~60 inline SVG definitions inside a single
`switch` statement, making the file extremely large and impossible to tree-shake.
Three separate icon systems coexist across the codebase:

1. **Icon.tsx inline SVGs** — 60+ icons defined as `case` branches in a monolithic
   switch. 41 of these use `fill={fill || '#1A2634'}`, which renders them
   invisible in dark mode.
2. **`web/components/svg/` directory** — 19 standalone SVG components
   (`UpgradeIcon.tsx`, `FeaturesIcon.tsx`, `UsersIcon.tsx`, etc.) with their own
   hardcoded fills (none use `currentColor`).
3. **IonIcon** — legacy icon set referenced in older components.

This triple system causes:

- **No tree-shaking** — importing `<Icon name="search" />` pulls in all 60 SVG
  definitions because they live in one switch statement.
- **Inconsistent API** — callers must know whether to use `<Icon>`,
  `<FeaturesIcon>`, or an IonIcon class. No single source of truth for available
  icons.
- **Dark mode breakage** — 41 icons default to `#1A2634` (near-black), invisible
  on the dark background (`#101628`). The `svg/` components also hardcode fills.
- **Maintenance burden** — adding a new icon means editing a 700+ line file and
  adding another `case` branch.

## Files

- `web/components/Icon.tsx` — monolithic icon switch (~60 cases)
- `web/components/svg/` — 19 standalone SVG components
- All consumers of `<Icon>` across the codebase (46+ files)

## Proposed Fix

### Step 1 — Extract each SVG to its own file

Create `web/components/icons/` directory. For each `case` in `Icon.tsx`, extract
the SVG markup into a standalone component file:

```
web/components/icons/
  ArrowLeftIcon.tsx
  ArrowRightIcon.tsx
  SearchIcon.tsx
  ...
  index.ts          ← barrel export + IconName type
```

Each extracted icon must:
- Accept `fill`, `width`, `height`, and spread `...rest` props
- Default `fill` to `currentColor` (not `#1A2634`)
- Use a consistent `FC<SVGProps<SVGSVGElement>>` type signature

### Step 2 — Migrate `svg/` directory icons into the new system

Move the 19 components from `web/components/svg/` into `web/components/icons/`,
normalising their API to match the new convention. Replace hardcoded fills with
`currentColor`.

### Step 3 — Create a new `Icon` wrapper (optional)

Keep the `<Icon name="search" />` API if desired, but implement it as a lazy
lookup into the barrel export rather than a switch statement. This preserves the
existing call-site API whilst enabling tree-shaking via dynamic imports or a
static map.

### Step 4 — Deprecate and remove IonIcon references

Grep for IonIcon usages, replace each with the equivalent new icon component,
then remove the IonIcon dependency.

### Step 5 — Update all import paths

Update all consumers to import from `components/icons/` (or continue using the
wrapper `<Icon>` component if kept).

## Acceptance Criteria

- [ ] No inline SVG definitions remain in `Icon.tsx` switch statement
- [ ] Every icon defaults to `fill="currentColor"` — no hardcoded hex fills
- [ ] `web/components/svg/` directory is empty or removed
- [ ] IonIcon is no longer referenced anywhere in the codebase
- [ ] `npm run typecheck` passes with no new errors
- [ ] `npm run build` completes; bundle size does not increase
- [ ] All icons are visible in both light and dark mode (verified in Storybook)
- [ ] Barrel export provides the `IconName` type for type-safe usage

## Dependencies

- Blocked by **QW-1** (Icon.tsx `currentColor` quick win) — apply that fix first,
  then this refactor builds on it
- Enables better Storybook coverage — individual icon files can each have a story
- Related to **LR-7** (dark mode full pass) — this resolves the icon portion of
  dark mode breakage

---
Part of the Design System Audit (#6606)
