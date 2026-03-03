# Design System Audit Plan (#6606)

## Context

The Flagsmith frontend design system was created a couple of years ago and some areas of the app have grown organically. This audit identifies inconsistencies — scanning the codebase for token misuse, dark mode gaps, and component fragmentation — to produce a structured report.

The team has no designers; the principal frontend engineer is the design system owner. The audit report will serve as both a bug list and a roadmap toward a consolidated design system.

## Output

- `frontend/DESIGN_SYSTEM_AUDIT.md` — code-first audit report (token misuse, dark mode gaps, component fragmentation)
- `frontend/DESIGN_SYSTEM_INVENTORY_GUIDE.md` — methodology and process guide for the visual inventory
- Penpot design file — visual inventory of every screen in both light and dark mode, grouped by feature area

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

Two complementary layers:

- **Visual inventory** — screenshot every screen in light and dark mode, group by feature area in Penpot. Makes inconsistencies visible at a glance and provides the visual evidence for each finding.
- **Code audit** — automated scanning of SCSS and TSX files for token misuse, combined with a manual component catalogue. Provides exact file paths, line numbers, and severity classifications.

Together they form a complete picture: the code audit identifies *what* is wrong and *where*, the visual inventory shows *why it matters*.

## Steps

### Phase 1 — Visual Inventory *(in progress)*

0. Publish this plan and comment on #6606 ✅
1. Screenshot every screen in **light mode** — all feature areas, key states (default, error, empty, loading)
2. Screenshot every screen in **dark mode** — same flows, focus on broken/missing dark mode styles
3. Organise screenshots in Penpot by feature area (Sign In, Projects, Segments, Audit Log, etc.) ✅ *(light mode done)*
4. Annotate inconsistencies directly in Penpot — mark visual issues side by side
5. Define canonical versions per component category

### Phase 2 — Code Audit *(in review)*

6. Colours audit — scan SCSS/TSX for hardcoded hex/rgb values ✅
7. Typography audit — scan for hardcoded font-size/weight/line-height ✅
8. Spacing audit — scan for hardcoded padding/margin/gap ✅
9. Button styles audit — check inline overrides and dark mode ✅
10. Form inputs audit — check state coverage and dark mode ✅
11. Icons audit — check hardcoded fills and dark mode ✅
12. Notifications audit — check toast/alert consistency ✅
13. Component inventory — catalogue all 11 categories ✅

### Phase 3 — Report & Review

14. Compile final report combining visual and code findings ✅ (code layer done, visual layer pending)
15. Move PR #6806 from DRAFT → ready for review
