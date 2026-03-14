---
title: "Remove legacy ErrorMessage.js and consolidate imports"
labels: ["design-system", "quick-win", "tech-debt"]
---

## Problem

The legacy class-based `web/components/ErrorMessage.js` coexists with its modern TypeScript replacement at `web/components/messages/ErrorMessage.tsx`.

37 files import from `components/ErrorMessage` (resolves to the legacy `.js` file). Only 2 files import from `components/messages/ErrorMessage` (the TS replacement).

> **Note:** The equivalent `SuccessMessage.js` duplication was already resolved in PR [#6873](https://github.com/Flagsmith/flagsmith/pull/6873), which deleted the legacy file and updated its 2 import sites.

## Files

- `web/components/ErrorMessage.js` — legacy class component (65 lines), **37 consumers**
- `web/components/messages/ErrorMessage.tsx` — TypeScript replacement (80 lines), 2 consumers

### Consumers to update

```
web/components/SimpleTwoFactor/prompt.js
web/components/SimpleTwoFactor/index.js
web/components/EditIdentity.tsx
web/components/tags/CreateEditTag.tsx
web/components/import-export/FeatureImport.tsx
web/components/NewVersionWarning.tsx
web/components/SamlForm.js
web/components/segments/Rule/components/RuleConditionRow.tsx
web/components/modals/ConfirmDeleteAccount.tsx
web/components/modals/CreateProject.js
web/components/modals/CreateSAML.tsx
web/components/mv/VariationOptions.tsx
web/components/modals/ChangeEmailAddress.tsx
web/components/modals/InviteUsers.tsx
web/components/modals/CreateMetadataField.tsx
web/components/UsersGroups.tsx
web/components/modals/CreateWebhook.js
web/components/modals/CreateAuditLogWebhook.tsx
web/components/modals/ConfirmDeleteRole.tsx
web/components/modals/CreateUser.tsx
web/components/modals/CreateTrait.tsx
web/components/modals/CreateEditIntegrationModal.tsx
web/components/modals/ForgotPasswordModal.tsx
web/components/modals/CreateWebhook.tsx
web/components/modals/create-feature/tabs/FeatureValue.tsx
web/components/modals/create-feature/tabs/CreateFeature.tsx
web/components/pages/AuditLogItemPage.tsx
web/components/modals/create-feature/index.js
web/components/pages/UsersAndPermissionsPage.tsx
web/components/pages/PasswordResetPage.js
web/components/pages/AccountSettingsPage.js
web/components/pages/admin-dashboard/AdminDashboardPage.tsx
web/components/pages/HomePage.tsx
web/components/pages/BrokenPage.tsx
web/components/pages/FeatureHistoryDetailPage.tsx
web/components/pages/ChangeRequestDetailPage.tsx
web/components/pages/CreateEnvironmentPage.tsx
```

## Proposed Fix

### Option A: Re-export shim (minimal diff)

1. Delete `web/components/ErrorMessage.js`
2. Create `web/components/ErrorMessage.tsx` as a re-export:
   ```tsx
   export { default } from 'components/messages/ErrorMessage'
   ```

This avoids updating 37 import paths in one commit. The shim can be removed in a follow-up that updates all paths.

### Option B: Direct migration (clean but large)

1. Delete `web/components/ErrorMessage.js`
2. Update all 37 imports from `components/ErrorMessage` → `components/messages/ErrorMessage`

Larger diff but no leftover shim.

### API compatibility

The TypeScript `ErrorMessage` has the same props as the legacy version (`error`, `errorMessageClass`, `errorStyles`, `enabledButton`), so it is a drop-in replacement.

## Verification

```bash
# Confirm legacy JS file is gone
ls web/components/ErrorMessage.js 2>&1
# Expected: No such file or directory

# Type check (will catch any prop mismatches)
npm run typecheck

# Lint
npx eslint --fix web/components/ErrorMessage.tsx

# Run unit tests
npm run test:unit
```

## Acceptance Criteria

- [ ] `web/components/ErrorMessage.js` is deleted
- [ ] All 37 consumers resolve to the TypeScript `ErrorMessage.tsx`
- [ ] `npm run typecheck` passes
- [ ] No runtime errors when triggering error messages

---
Part of the Design System Audit (#6606)
SuccessMessage.js consolidation: PR #6873
