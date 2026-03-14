---
title: "Install @storybook/addon-a11y for component-level accessibility checks"
labels: ["design-system", "medium-effort", "accessibility", "storybook"]
---

## Problem

The Storybook configuration already includes `@storybook/addon-a11y` in
`.storybook/main.js` (line 9) and `package.json` lists it as a dependency.
However, the addon is not being used effectively because **6 of 9 audited UI
categories have no Storybook stories at all**:

| Category | Stories | Status |
|----------|---------|--------|
| Icons | Yes | Covered |
| Colours | Yes | Covered |
| Buttons | Yes | Covered (but uses raw `<button>` HTML, not the real component — see QW-10) |
| Dark Mode Issues | Yes | Covered |
| Typography | Yes | Covered |
| **Forms/Inputs** | **No** | Missing |
| **Modals** | **No** | Missing |
| **Tables** | **No** | Missing |
| **Tooltips** | **No** | Missing |
| **Notifications/Alerts** | **No** | Missing |
| **Navigation** | **No** | Missing |

Without stories, the a11y addon cannot surface WCAG issues for the majority of
the component library. The audit identified multiple accessibility failures
(contrast ratios, missing focus rings, invisible icons) that would have been
caught automatically if stories existed.

## Files

- `frontend/.storybook/main.js` — addon already configured (no changes needed)
- `frontend/stories/` — new story files to create

## Proposed Fix

### 1. Verify the addon works with existing stories

```bash
npm run storybook
# Open any existing story → check the "Accessibility" panel in the addon bar
```

### 2. Create stories for uncovered categories

Priority order (most a11y issues first):

**Forms/Inputs** — `stories/Forms.stories.tsx`
- Text input (default, focused, disabled, read-only, error states)
- Textarea (default, dark mode border issue)
- Checkbox (unchecked, checked, focused, disabled)
- Switch (off, on, focused, disabled)
- Select dropdown

**Notifications/Alerts** — `stories/Notifications.stories.tsx`
- Toast (success, danger)
- ErrorMessage, SuccessMessage, InfoMessage, WarningMessage
- Both light and dark mode variants

**Modals** — `stories/Modals.stories.tsx`
- Confirmation modal
- Standard modal with form content
- Focus trap behaviour

**Navigation** — `stories/Navigation.stories.tsx`
- Sidebar links (active, inactive, with icons)
- Tab menu

**Tables** — `stories/Tables.stories.tsx`
- PanelSearch with sample data
- Table with sortable columns

**Tooltips** — `stories/Tooltips.stories.tsx`
- Default tooltip
- Tooltip with long content

### 3. Configure a11y rules

Optionally add a `preview.js` parameter to set the axe-core rules:

```js
// .storybook/preview.js
export const parameters = {
  a11y: {
    config: {
      rules: [
        { id: 'color-contrast', enabled: true },
        { id: 'focus-visible', enabled: true },
      ],
    },
  },
}
```

## Verification

```bash
# Launch Storybook and check the Accessibility panel for each new story
npm run storybook

# Confirm addon surfaces known issues (e.g. contrast on secondary text)
```

## Acceptance Criteria

- [ ] `@storybook/addon-a11y` panel appears in Storybook UI (already configured)
- [ ] Forms/Inputs stories exist and render real components
- [ ] Notifications/Alerts stories exist covering toast and message components
- [ ] At least 4 of the 6 missing categories have initial stories
- [ ] Each new story renders in both light and dark mode
- [ ] Known a11y issues (contrast, focus rings) are surfaced in the addon panel
- [ ] No new `npm run build` or `npm run storybook` errors

---
Part of the Design System Audit (#6606)
