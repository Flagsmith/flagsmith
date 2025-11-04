# UI Patterns & Best Practices

## Table Components

### Pattern: Reusable Table Components

**Location:** `components/project/tables/`

Tables should be self-contained components that fetch their own data and handle loading/error states.

**Example:** `InvoiceTable.tsx`

```typescript
import { useGetInvoicesQuery } from 'common/services/useInvoice'
import { useDefaultSubscription } from 'common/services/useDefaultSubscription'
import Loader from 'components/base/Loader'
import { ErrorMessage } from 'components/base/Messages'
import ContentContainer from './ContentContainer'

const InvoiceTable: FC = () => {
  const { defaultSubscriptionId } = useDefaultSubscription()
  const { data: invoices, error, isLoading } = useGetInvoicesQuery({
    subscription_id: `${defaultSubscriptionId}`,
  })

  if (isLoading) {
    return (
      <div className='d-flex justify-content-center'>
        <Loader />
      </div>
    )
  }

  if (error) return <ErrorMessage>{error}</ErrorMessage>

  return (
    <ContentContainer>
      <table className='invoice-table'>
        <thead>
          <tr>
            <th>Invoice No.</th>
            <th className='d-none d-md-table-cell'>Description</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {invoices?.map((invoice) => (
            <tr key={invoice.id}>
              <td>{invoice.id}</td>
              <td className='d-none d-md-table-cell'>{invoice.description}</td>
              <td>{invoice.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </ContentContainer>
  )
}
```

### Responsive Tables

Use Bootstrap classes for responsive behavior:
- `d-none d-md-table-cell` - Hide column on mobile
- `d-block d-md-none` - Show on mobile only

## Tabs Component

**Location:** `components/base/forms/Tabs.tsx`

### Basic Usage

```typescript
import { useState } from 'react'
import { Tabs } from 'components/base/forms/Tabs'

const MyPage = () => {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <Tabs
      value={activeTab}
      onChange={setActiveTab}
      tabLabels={['Tab 1', 'Tab 2', 'Tab 3']}
    >
      <div>Tab 1 content</div>
      <div>Tab 2 content</div>
      <div>Tab 3 content</div>
    </Tabs>
  )
}
```

### Tabs with Feature Flag (Optional)

**Note:** Only use feature flags when explicitly requested. By default, implement features directly without flags.

When specifically requested, this pattern shows tabs only when feature flag is enabled:

```typescript
import { useFlags } from 'flagsmith/react'
import { Tabs } from 'components/base/forms/Tabs'

const MyPage = () => {
  const { my_feature_flag } = useFlags(['my_feature_flag'])
  const [activeTab, setActiveTab] = useState(0)

  return (
    <div>
      <h2>My Section</h2>
      {my_feature_flag?.enabled ? (
        <Tabs
          value={activeTab}
          onChange={setActiveTab}
          tabLabels={['Default', 'New Feature']}
        >
          <div><ExistingComponent /></div>
          <div><NewComponent /></div>
        </Tabs>
      ) : (
        <ExistingComponent />
      )}
    </div>
  )
}
```

See `feature-flags.md` for more details on when and how to use feature flags.

### Uncontrolled Tabs

For simple cases without parent state management:

```typescript
<Tabs uncontrolled tabLabels={['Tab 1', 'Tab 2']}>
  <div>Tab 1 content</div>
  <div>Tab 2 content</div>
</Tabs>
```

## Confirmation Dialogs

**NEVER use `window.confirm`** - Always use the `openConfirm` function from `components/base/Modal`.

### Correct Usage

```typescript
import { openConfirm } from 'components/base/Modal'

// Signature: openConfirm(title, body, onYes, onNo?, challenge?)
openConfirm(
  'Delete Partner',
  'Are you sure you want to delete this partner?',
  async (closeModal) => {
    const res = await deleteAction()
    if (!res.error) {
      toast(null, 'Partner deleted successfully')
      closeModal() // Always call closeModal to dismiss the dialog
    }
  },
)
```

### Parameters
- `title: string` - Dialog title
- `body: ReactNode` - Dialog content (can be JSX)
- `onYes: (closeModal: () => void) => void` - Callback when user confirms
- `onNo?: () => void` - Optional callback when user cancels
- `challenge?: string` - Optional challenge text user must type to confirm

### Key Points
- The `onYes` callback receives a `closeModal` function
- Always call `closeModal()` when the action completes successfully
- Can be async - use `async (closeModal) => { ... }`

## Backend Integration

### Always Run API Types Sync Before API Work

When using `/api` to generate new API services, the command automatically runs `/api-types-sync` first to:
1. Pull latest backend changes (`git pull` in `../hoxtonmix-api`)
2. Sync frontend types with backend serializers
3. Ensure types are up-to-date before generating new services

This prevents type mismatches and ensures consistency.
