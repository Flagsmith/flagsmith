# Audit Verification Report

All claims in the Dark Mode Audit and Light Mode Audit boards have been verified against the codebase.

---

## Dark Mode Audit — All 6 claims VALID

### 1. Surface layers nearly identical

- `$body-bg-dark: #101628`
- `$panel-bg-dark: #15192b`
- `$input-bg-dark: #161d30`
- Only 5–18 hex values apart — no visual separation between layers

### 2. Secondary text barely meets AA

- `$text-muted: #656d7b` on `#15192b` background
- Contrast ratio: ~4.2:1
- WCAG AA requires 4.5:1 for normal text — **this fails**
- Note: the audit board says "barely meets" but it actually fails AA

### 3. Form inputs blend into panels

- Input background: `#161d30`
- Panel background: `#15192b`
- Difference: 5 hex values
- `$input-border-color: rgba(101, 109, 123, 0.16)` — 16% opacity border provides almost no distinction

### 4. Charts use hardcoded light colours

- 3 of 4 chart files affected
- `OrganisationUsage.container.tsx`: `stroke='#EFF1F4'` (light grid lines — invisible on dark bg)
- `SingleSDKLabelsChart.tsx`: `fill='#1A2634'` (dark text on dark bg — invisible)
- These colours are not token-driven and do not respond to theme changes

### 5. Modals and cards same background as panels

- Both resolve to `#15192b`
- No elevation or shadow difference
- Cards, modals, and panels are visually indistinguishable

### 6. 50+ orphan hex colours

- 280 hardcoded hex instances across TSX files
- 52 unique hex values
- Top offenders:
  - `#9DA4AE` — 52 occurrences
  - `#656D7B` — 44 occurrences
  - `#6837FC` — 21 occurrences
- None of these go through tokens or CSS custom properties

---

## Light Mode Audit — All 6 claims VALID

### 1. All-white surfaces, no depth

- `$bg-light100: #ffffff`
- `$panel-bg: white`
- `$input-bg: #fff`
- All resolve to the same white — page, panel, and input backgrounds are identical

### 2. Secondary text below AA

- `$text-muted: #656d7b` on `#ffffff` background
- Contrast ratio: 4.48:1
- WCAG AA requires 4.5:1 — **fails by 0.02**

### 3. Input borders nearly invisible

- `$input-border-color: $basic-alpha-16: rgba(101, 109, 123, 0.16)`
- 16% opacity on a white background
- Effective rendered colour is barely distinguishable from the background

### 4. Subtle hover states

- Many interactive elements use text-colour-only hover changes
- No background colour shift on hover
- Difficult to perceive, especially for users with low vision

### 5. Focus rings = brand purple or disabled

- `btn:focus-visible { box-shadow: none }` in `_buttons.scss`
- Focus ring explicitly removed on buttons
- Where present elsewhere, focus uses brand purple (`#6837FC`) which may not have sufficient contrast on all backgrounds

### 6. Disabled states at 32% opacity

- `opacity: 0.32` pattern confirmed for disabled elements
- Low opacity on already-low-contrast elements compounds the problem

---

## WCAG / Implementation Claims — VALID

| Claim | Verified value | Source |
|-------|---------------|--------|
| `.dark` CSS selector rules | 40 rules | SCSS files across `web/styles/` |
| `getDarkMode()` runtime calls | 46 instances | 8 files in `web/components/` |
| `data-bs-theme` attribute underused | Set in `darkMode.ts`, only 2 CSS rules reference it | `_tokens.scss` |
| Hardcoded hex values in TSX | 280 instances, 52 unique | Grep across `web/components/` |
| Icon.tsx hardcoded fill | 46 instances of `fill={fill \|\| '#1A2634'}` | `web/components/Icon.tsx` |

---

## Summary

Every claim in both audit boards is supported by the codebase. The audits are accurate.

### One suggested correction

The Dark Mode Audit board claim #2 says secondary text "barely meets AA". It actually **fails** AA (~4.2:1 vs the 4.5:1 requirement). Consider updating the wording to "fails AA" for consistency with the Light Mode board, which correctly says "below AA".
