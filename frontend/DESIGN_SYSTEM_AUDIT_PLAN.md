# Design System Audit Plan (#6606)

## Context

The Flagsmith frontend design system was created a couple of years ago and some areas of the app have grown organically. This audit identifies inconsistencies — scanning the codebase for token misuse, dark mode gaps, and component fragmentation — to produce a structured report.

The team has no designers; the principal frontend engineer is the design system owner. The audit report will serve as both a bug list and a roadmap toward a proper Storybook-based design system.

## Output

A single markdown report: `frontend/DESIGN_SYSTEM_AUDIT.md` — report only, no code changes.

### Part A — Component Inventory

A catalogue of every recurring UI pattern, documenting what exists, where, how many variants, and consolidation opportunities. Categories:

1. Modals/Dialogs
2. Menus/Dropdowns
3. Selects
4. Toasts/Notifications
5. Tables & Filters
6. Tabs
7. Buttons
8. Icons
9. Empty States
10. Tooltips
11. Layout

### Part B — Token & Consistency Findings

Organised by the 7 areas from issue #6606:

1. **Colours** — Hardcoded hex/rgb values, missing dark mode overrides
2. **Typography** — Hardcoded font-size/weight/line-height bypassing type scale
3. **Spacing** — Hardcoded padding/margin/gap values
4. **Button styles** — Inline overrides, dark mode gaps
5. **Form inputs** — State coverage, dark mode gaps
6. **Icons** — Hardcoded fills, dark mode responsiveness
7. **Notifications** — Toast/alert styling consistency

### Severity levels

- **P0**: Broken in dark mode or accessibility issue
- **P1**: Visual inconsistency with the token system
- **P2**: Token hygiene (hardcoded value that should use a variable)

## Approach

Code-first audit — no Figma access required. Automated scanning of SCSS and TSX files for token misuse, combined with manual component catalogue.

## Steps

0. Publish this plan and comment on #6606
1. Colours audit — scan SCSS/TSX for hardcoded hex/rgb values
2. Typography audit — scan for hardcoded font-size/weight/line-height
3. Spacing audit — scan for hardcoded padding/margin/gap
4. Button styles audit — check inline overrides and dark mode
5. Form inputs audit — check state coverage and dark mode
6. Icons audit — check hardcoded fills and dark mode
7. Notifications audit — check toast/alert consistency
8. Component inventory — catalogue all 11 categories
9. Compile final report
