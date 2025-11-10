# Quick Reference Guide

## Common Tasks Checklist

### Finding a Page Component

**All page components are in `web/components/pages/`** - no need to search extensively.

Examples:
- Features page: `web/components/pages/FeaturesPage.js`
- Project settings: `web/components/pages/ProjectSettingsPage.js`
- Environment settings: `web/components/pages/EnvironmentSettingsPage.tsx`
- Users: `web/components/pages/UsersPage.tsx`

To find a page:
```bash
ls web/components/pages/ | grep -i <keyword>
```

### Adding a New API Endpoint

- [ ] Check backend for endpoint (see `backend-integration.md`)
- [ ] Add request type to `common/types/requests.ts`
- [ ] Add/extend RTK Query service in `common/services/use*.ts`
- [ ] Export hook from service
- [ ] Use hook in component with proper loading/error handling
- [ ] Run linter: `npx eslint --fix <files>`

### Creating a New Table Component

- [ ] Create in `components/project/tables/`
- [ ] Fetch data with RTK Query hook
- [ ] Handle loading state with `<Loader />`
- [ ] Handle error state with `<ErrorMessage>`
- [ ] Wrap table in `<ContentContainer>`
- [ ] Use responsive classes: `d-none d-md-table-cell`

### Adding Tabs to a Page

- [ ] Import `{ Tabs }` from `components/base/forms/Tabs`
- [ ] Add `useState` for active tab
- [ ] Pass `value`, `onChange`, and `tabLabels` props
- [ ] Wrap each tab content in `<div>`

### Implementing Feature Flags (When Requested)

Only use feature flags when explicitly requested by the user.

- [ ] Create flag in Flagsmith (use `/feature-flag` command or MCP tools)
- [ ] In render method or component, call `Utils.getFlagsmithHasFeature('flag_name')`
- [ ] Store result in a variable (e.g., `const isEnabled = Utils.getFlagsmithHasFeature('flag_name')`)
- [ ] Use conditional rendering: `{isEnabled && <Component />}`
- [ ] Provide fallback when flag is disabled
- [ ] Enable flag manually via Flagsmith UI at https://app.flagsmith.com

## File Locations

| Purpose | Location | Example |
|---------|----------|---------|
| API Services | `common/services/use*.ts` | `useEnvironment.ts`, `useFeature.ts` |
| Request Types | `common/types/requests.ts` | API request interfaces |
| Response Types | `common/types/responses.ts` | API response interfaces |
| Table Components | `components/project/tables/` | User tables, data grids |
| **Page Components** | **`web/components/pages/`** | **`FeaturesPage.js`, `ProjectSettingsPage.js`** |
| Card Components | `components/project/cards/` | Summary cards, info cards |
| Base UI Components | `components/base/` | Buttons, forms, inputs |
| Feature Flags Context | `.claude/context/feature-flags.md` | Flagsmith integration guide |
| Backend API | `../api/` | Flagsmith backend API |

## Common Components for Messages

| Component | Location | Usage |
|-----------|----------|-------|
| InfoMessage | `components/InfoMessage` | Info alerts/messages |
| ErrorMessage | `components/base/Messages` | Error states |
| SuccessMessage | `components/base/Messages` | Success notifications |
| Loader | `components/base/Loader` | Loading states |
| Tooltip | `components/Tooltip` | Hover tooltips |
| Button | `components/base/forms/Button` | Standard buttons |

## Common Imports

### RTK Query
```typescript
import { service } from 'common/service'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
```

### UI Components
```typescript
import { Tabs } from 'components/base/forms/Tabs'
import Loader from 'components/base/Loader'
import { ErrorMessage } from 'components/base/Messages'
```

### Hooks
```typescript
import { useDefaultSubscription } from 'common/services/useDefaultSubscription'
import { useState } from 'react'
```

### Utils
```typescript
import { Format } from 'common/utils/format'
import dayjs from 'dayjs'
```

## Backend API Structure

```
../api/apps/
├── projects/          # Projects and features
├── environments/      # Environment management
├── features/          # Feature flags
├── segments/          # User segments
├── users/            # User management
├── organisations/    # Organization management
├── permissions/      # Access control
└── audit/           # Audit logs
```

## Common Backend Endpoints

See `/backend` slash command to search the backend codebase for specific endpoints.

## RTK Query Patterns

### Query (GET)
```typescript
builder.query<Res['entity'], Req['getEntity']>({
  providesTags: [{ id: 'LIST', type: 'Entity' }],
  query: (req) => ({
    url: `endpoint/${req.id}`,
  }),
})
```

### Mutation (POST/PUT/DELETE)
```typescript
builder.mutation<Res['entity'], Req['updateEntity']>({
  invalidatesTags: [{ id: 'LIST', type: 'Entity' }],
  query: (req) => ({
    body: req,
    method: 'PUT',
    url: `endpoint/${req.id}`,
  }),
})
```

### Skip Query
```typescript
useGetEntityQuery(
  { id: entityId },
  { skip: !entityId }  // Don't run query if no ID
)
```

## Component Patterns

### Loading State
```typescript
if (isLoading) {
  return (
    <div className='d-flex justify-content-center'>
      <Loader />
    </div>
  )
}
```

### Error State
```typescript
if (error) return <ErrorMessage>{error}</ErrorMessage>
```

### Feature Flag Check
```typescript
const isFeatureEnabled = Utils.getFlagsmithHasFeature('flag_name')
if (isFeatureEnabled) {
  // Show new feature
}
```

## Slash Commands

| Command | Purpose |
|---------|---------|
| `/api-types-sync` | Sync types with backend |
| `/api` | Generate new API service |
| `/backend <search>` | Search backend codebase |
| `/feature-flag` | Create feature flag |
| `/form` | Generate form with Yup + Formik |
| `/check` | Run type checking and linting |
| `/context` | Load specific context files |

## Common Utilities

### Date Formatting
```typescript
import dayjs from 'dayjs'
dayjs(timestamp).format('DD MMM YY')
```

### Money Formatting
```typescript
import { Format } from 'common/utils/format'
Format.money(amountInCents)  // e.g., "$12.34"
Format.camelCase('pending_payment')  // e.g., "Pending Payment"
```

### Subscription Info
```typescript
const { defaultSubscriptionId, subscriptionDetail, hasPermission } =
  useDefaultSubscription()

const canManageBilling = hasPermission('MANAGE_BILLING')
const companyId = subscriptionDetail?.company_id
```

## Bootstrap Classes Reference

### Responsive Display
- `d-none d-md-block` - Hide on mobile, show on desktop
- `d-block d-md-none` - Show on mobile, hide on desktop
- `d-none d-md-table-cell` - For table cells

### Spacing
- `mt-4` - Margin top
- `mb-4` - Margin bottom
- `pb-4` - Padding bottom
- `mb-24` - Large margin bottom

### Layout
- `container-fluid` - Full-width container
- `row` - Bootstrap row
- `col-lg-6 col-md-12` - Responsive columns

### Flexbox
- `d-flex` - Display flex
- `justify-content-center` - Center horizontally
- `align-items-center` - Center vertically

## Linting

Always run linter after changes:
```bash
npx eslint --fix common/types/requests.ts
npx eslint --fix common/services/useInvoice.ts
npx eslint --fix components/project/tables/MyTable.tsx
npx eslint --fix pages/my-page.tsx
```

Or use the check command:
```bash
/check
```

## Git Workflow

Check backend branches:
```bash
cd ../api
git fetch
git log --oneline origin/feat/branch-name -n 10
git show COMMIT_HASH:path/to/file.py
```

## Debugging Tips

### Check if query is running
```typescript
const { data, error, isLoading, isFetching } = useGetEntityQuery(...)
console.log({ data, error, isLoading, isFetching })
```

### Check feature flag value
```typescript
const isEnabled = Utils.getFlagsmithHasFeature('my_flag')
console.log('Flag enabled:', isEnabled)
```

### Inspect Redux state
```typescript
import { getStore } from 'common/store'
console.log(getStore().getState())
```

### Force refetch
```typescript
const { refetch } = useGetEntityQuery(...)
refetch()
```
