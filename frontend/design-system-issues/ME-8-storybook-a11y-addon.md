---
title: "Add @storybook/addon-a11y for component-level contrast checks"
labels: ["design-system", "medium-effort", "accessibility"]
---

## Problem

Storybook has visual stories for design system components but no automated accessibility checking. Developers can only spot contrast and accessibility issues by eye. The existing axe-core E2E tests (added in #6562) operate at the page level and do not surface component-level violations during development.

Without this addon, accessibility regressions in individual components are invisible until they reach a full page test — or until a user reports them.

## Files

- `.storybook/main.ts` — addon registration
- `.storybook/preview.ts` — optional: configure a11y rules globally (e.g. WCAG 2.1 AA)
- `package.json` — new dev dependency

## Proposed Fix

1. Install `@storybook/addon-a11y` as a dev dependency:

```bash
npm install --save-dev @storybook/addon-a11y
```

2. Register the addon in `.storybook/main.ts`:

```ts
addons: [
  // existing addons...
  '@storybook/addon-a11y',
],
```

3. Optionally configure WCAG 2.1 AA as the default ruleset in `.storybook/preview.ts`.

## Acceptance Criteria

- [ ] `@storybook/addon-a11y` installed and registered
- [ ] An "Accessibility" tab appears in the Storybook addon panel for every story
- [ ] Accessibility violations are flagged automatically in the panel (not just manually checked)
- [ ] No existing Storybook stories broken by the addition
- [ ] `npm run typecheck` and `npm run lint` pass

## Storybook Validation

Any story → open the "Accessibility" tab in the addon panel → violations and passes listed automatically. Verify against a known contrast issue (e.g. a story with a light grey label on white) to confirm the addon is catching real violations.

## Dependencies

None. Complements but does not depend on ME-9 (expand E2E a11y coverage).

---
Part of the Design System Audit (#6606)
