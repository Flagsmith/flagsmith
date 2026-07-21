# Common Code Patterns

> For API patterns, see [api.md](api.md). For mobile patterns, see [mobile.md](mobile.md).

## Complete Feature Implementation Example

This end-to-end example shows how to add tabs with a new API endpoint (real implementation from the codebase).

**Requirements:** Add a "Top-Up" invoices tab to the account-billing page, pulling from a new backend endpoint.

### Step 1: Check Backend API

```bash
cd ../api
git fetch
git show COMMIT_HASH:apps/customers/urls.py | grep "invoice"
# Found: path("companies/<int:company_id>/invoices", get_company_invoices)
```

### Step 2: Add Request Type

**File:** `common/types/requests.ts`

```typescript
export type Req = {
  // ... existing types
  getCompanyInvoices: {
    company_id: string
  }
}
```

### Step 3: Extend RTK Query Service

**File:** `common/services/useInvoice.ts`

```typescript
export const invoiceService = service
  .enhanceEndpoints({ addTagTypes: ['Invoice'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getCompanyInvoices: builder.query<
        Res['invoices'],
        Req['getCompanyInvoices']
      >({
        providesTags: [{ id: 'LIST', type: 'Invoice' }],
        query: (req) => ({
          url: `customers/companies/${req.company_id}/invoices`,
        }),
        transformResponse(res: InvoiceSummary[]) {
          return res?.map((v) => ({ ...v, date: v.date * 1000 }))
        },
      }),
    }),
  })

export const {
  useGetCompanyInvoicesQuery,
  // END OF EXPORTS
} = invoiceService
```

### Step 4: Create Table Component

**File:** `components/project/tables/CompanyInvoiceTable.tsx`

```typescript
import { useGetCompanyInvoicesQuery } from 'common/services/useInvoice'
import { useDefaultSubscription } from 'common/services/useDefaultSubscription'

const CompanyInvoiceTable: FC = () => {
  const { subscriptionDetail } = useDefaultSubscription()
  const companyId = subscriptionDetail?.company_id

  const { data: invoices, error, isLoading } = useGetCompanyInvoicesQuery(
    { company_id: `${companyId}` },
    { skip: !companyId }
  )

  if (isLoading) return <Loader />
  if (error) return <ErrorMessage>{error}</ErrorMessage>

  return (
    <ContentContainer>
      <table className='invoice-table'>
        {/* table structure */}
      </table>
    </ContentContainer>
  )
}
```

### Step 5: Add Tabs to Page

**File:** `pages/account-billing.tsx`

```typescript
import { useState } from 'react'
import { Tabs } from 'components/base/forms/Tabs'
import InvoiceTable from 'components/project/tables/InvoiceTable'
import CompanyInvoiceTable from 'components/project/tables/CompanyInvoiceTable'

const AccountAndBilling = () => {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <div>
      <h2>Invoices</h2>
      <Tabs
        value={activeTab}
        onChange={setActiveTab}
        tabLabels={['Subscription', 'Top-Up']}
      >
        <div><InvoiceTable /></div>
        <div><CompanyInvoiceTable /></div>
      </Tabs>
    </div>
  )
}
```

### Step 6: Run Linter

```bash
npx eslint --fix common/types/requests.ts common/services/useInvoice.ts \
  components/project/tables/CompanyInvoiceTable.tsx pages/account-billing.tsx
```

**Done!** The feature is now live with tabs and proper error handling.

### Optional: Add Feature Flag

If you need to gate this feature behind a feature flag (only when explicitly requested), see `feature-flags/` for the pattern.

## Import Rules

**ALWAYS use path aliases - NEVER use relative imports**

```typescript
// ✅ Correct
import { service } from 'common/service'
import { Button } from 'components/base/forms/Button'
import { validateForm } from 'project/utils/forms/validateForm'

// ❌ Wrong
import { service } from '../service'
import { Button } from '../../base/forms/Button'
import { validateForm } from '../../../utils/forms/validateForm'
```

## Pre-commit Checks

Before committing, run:

```bash
npm run check:staged
```

This runs:
1. TypeScript type checking on staged files
2. ESLint with auto-fix on staged files

Or use the slash command:

```
/check-staged
```
