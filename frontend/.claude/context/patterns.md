# Common Code Patterns

## Complete Feature Implementation Example

This end-to-end example shows how to add tabs with a new API endpoint (real implementation from the codebase).

**Requirements:** Add a "Top-Up" invoices tab to the account-billing page, pulling from a new backend endpoint.

### Step 1: Check Backend API

```bash
cd ../hoxtonmix-api
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

If you need to gate this feature behind a feature flag (only when explicitly requested), see `feature-flags.md` for the pattern.

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

## Mobile-Specific Patterns

### Toast Notifications (Mobile)

Mobile uses `react-native-toast-message`:

```typescript
// ✅ Correct for mobile
import Toast from 'react-native-toast-message'

Toast.show({ text1: 'Success message' })
Toast.show({ text1: 'Error message', type: 'error' })

// ❌ Wrong - this is web only
import { toast } from 'components/base/Toast'
toast('Success', 'Message')
```

### Icons (Mobile)

Mobile uses specific SVG component imports, not a generic Icon component:

```typescript
// ✅ Correct for mobile
import EditIcon from 'components/svgs/EditIcon'
import RemoveIcon from 'components/svgs/RemoveIcon'
import IconButton from 'components/IconButton'

<IconButton icon={<EditIcon />} onPress={handleEdit} />
<IconButton icon={<RemoveIcon />} onPress={handleDelete} />

// ❌ Wrong - this is web only
import Icon from 'project/Icon'
<Icon name='edit' fill='primary' />
```

### Confirm Dialogs (Mobile)

Mobile uses Alert or the utility function:

```typescript
// ✅ Correct for mobile
import openConfirm from 'components/utility-components/openConfirm'

openConfirm(
  'Delete Item',
  'Are you sure you want to delete this item?',
  () => handleDelete(),
)

// ❌ Wrong - this is web only
import { openConfirm } from 'components/base/Modal'
openConfirm('Title', <JSXContent />, callback)
```

### Component Naming (Mobile)

Follow existing mobile patterns:

```typescript
// Mobile components in mobile/app/components/
- MailTable.tsx (not MailList)
- TeamTable.tsx
- WhatsAppTable.tsx
- CreateEditNumber.tsx (modal for creating/editing)
- Custom modals use CustomModal component
```

### Modal-Based CRUD Pattern

For list components with create/edit capabilities, use a single modal for both operations:

```typescript
import { useState } from 'react'
import CreateEditModal from './CreateEditModal'

const MyTable: FC = () => {
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<ItemType | null>(null)

  const handleEdit = (item: ItemType) => {
    setEditing(item)
    setModalOpen(true)
  }

  const handleCreate = () => {
    setEditing(null)  // null = create mode
    setModalOpen(true)
  }

  return (
    <>
      <Button onPress={handleCreate}>Add Item</Button>

      {items?.map((item) => (
        <View key={item.id}>
          {!item.cancelled_on && (
            <IconButton
              onPress={() => handleEdit(item)}
              icon={<EditIcon />}
            />
          )}
        </View>
      ))}

      <CreateEditModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        initial={editing}  // null for create, data for edit
      />
    </>
  )
}
```

**Modal component pattern:**
```typescript
type Props = {
  isOpen: boolean
  onClose: () => void
  initial?: ItemType | null  // null/undefined = create, data = edit
  onSuccess?: () => void
}

const CreateEditModal: FC<Props> = ({ isOpen, onClose, initial }) => {
  const [createItem] = useCreateItemMutation()
  const [updateItem] = useUpdateItemMutation()

  const [form, setForm] = useState({
    field1: initial?.field1 || '',
    field2: initial?.field2 || '',
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen && initial) {
      setForm({ field1: initial.field1, field2: initial.field2 })
    } else if (isOpen && !initial) {
      setForm({ field1: '', field2: '' })
    }
  }, [isOpen, initial])

  const handleSubmit = async () => {
    if (initial) {
      await updateItem({ id: initial.id, ...form })
    } else {
      await createItem(form)
    }
    onClose()
  }

  return (
    <CustomModal
      visible={isOpen}
      onDismissPress={onClose}
      title={initial ? 'Edit Item' : 'Create Item'}
    >
      {/* form fields */}
    </CustomModal>
  )
}
```

**Key principles:**
- Single modal handles both create and edit
- `initial` prop determines mode (null = create, data = edit)
- Reset form state when modal opens
- Different mutation based on mode
- Button text changes based on mode

## API Service Patterns

### Query vs Mutation Rule

- **GET requests** → `builder.query`
- **POST/PUT/PATCH/DELETE requests** → `builder.mutation`

```typescript
// ✅ Correct: GET endpoint
getMailItem: builder.query<Res['mailItem'], Req['getMailItem']>({
  providesTags: (res, _, req) => [{ id: req?.id, type: 'MailItem' }],
  query: (query: Req['getMailItem']) => ({
    url: `mailbox/mails/${query.id}`,
  }),
}),

// ✅ Correct: POST endpoint
createScanMail: builder.mutation<Res['scanMail'], Req['createScanMail']>({
  invalidatesTags: [{ id: 'LIST', type: 'ScanMail' }],
  query: (query: Req['createScanMail']) => ({
    body: query,
    method: 'POST',
    url: `mailbox/mails/${query.id}/actions/scan`,
  }),
}),
```

### File Download Pattern

Use the reusable `handleFileDownload` utility for endpoints that return files:

```typescript
import { handleFileDownload } from 'common/utils/fileDownload'

getInvoiceDownload: builder.query<Res['invoiceDownload'], Req['getInvoiceDownload']>({
  query: (query: Req['getInvoiceDownload']) => ({
    url: `customers/invoices/${query.id}/download`,
    responseHandler: (response) => handleFileDownload(response, 'invoice.pdf'),
  }),
}),
```

## Pagination Pattern

Use `useInfiniteScroll` hook for paginated lists:

```typescript
import useInfiniteScroll from 'common/hooks/useInfiniteScroll'
import { useGetMailQuery } from 'common/services/useMail'

const MailList = ({ subscription_id }: Props) => {
  const {
    data,
    isLoading,
    isFetching,
    loadMore,
    refresh,
    searchItems,
  } = useInfiniteScroll(
    useGetMailQuery,
    { subscription_id, page_size: 20 },
  )

  return (
    <InfiniteScroll
      dataLength={data?.results?.length || 0}
      next={loadMore}
      hasMore={!!data?.next}
      loader={<Spinner />}
      refreshFunction={refresh}
      pullDownToRefresh
    >
      {data?.results.map(item => <MailCard key={item.id} {...item} />)}
    </InfiniteScroll>
  )
}
```

## Error Handling

### RTK Query Error Pattern

```typescript
const [createMail, { isLoading, error }] = useCreateMailMutation()

const handleSubmit = async () => {
  try {
    const result = await createMail(data).unwrap()
    // Success - result contains the response
    toast.success('Mail created successfully')
  } catch (err) {
    // Error handling
    if ('status' in err) {
      // FetchBaseQueryError
      const errMsg = 'error' in err ? err.error : JSON.stringify(err.data)
      toast.error(errMsg)
    } else {
      // SerializedError
      toast.error(err.message || 'An error occurred')
    }
  }
}
```

### Query Refetching

```typescript
const { data, refetch } = useGetMailQuery({ id: '123' })

// Refetch on demand
const handleRefresh = () => {
  refetch()
}

// Automatic refetch on focus/reconnect is enabled by default in common/service.ts
```

## Cache Invalidation

### Manual Cache Clearing

```typescript
import { getStore } from 'common/store'
import { mailItemService } from 'common/services/useMailItem'

export const clearMailCache = () => {
  getStore().dispatch(
    mailItemService.util.invalidateTags([{ type: 'MailItem', id: 'LIST' }])
  )
}
```

### Automatic Invalidation

Cache invalidation is handled automatically through RTK Query tags:

```typescript
// Mutation invalidates the list
createMail: builder.mutation<Res['mail'], Req['createMail']>({
  invalidatesTags: [{ type: 'Mail', id: 'LIST' }],
  // This will automatically refetch any active queries with matching tags
}),
```

## Type Organization

### Request and Response Types

All API types go in `common/types/`:

```typescript
// common/types/requests.ts
export type Req = {
  getMail: PagedRequest<{
    subscription_id: string
    q?: string
  }>
  createMail: {
    id: string
    content: string
  }
  // END OF TYPES
}

// common/types/responses.ts
export type Res = {
  mail: PagedResponse<Mail>
  mailItem: MailItem
  // END OF TYPES
}
```

### Shared Types

For types used across requests AND responses, keep them in their respective files but document the shared usage:

```typescript
// common/types/requests.ts
export type Address = {
  address_line_1: string
  address_line_2: string | null
  postal_code: string
  city: string
  country: string
}
```

## SSG CLI Usage

Always use `npx ssg` to generate new API services:

```bash
# Interactive mode
npx ssg

# Follow prompts to:
# 1. Choose action type (get/create/update/delete)
# 2. Enter resource name
# 3. Enter API endpoint URL
# 4. Configure cache invalidation
```

The CLI will:
- Create/update service file in `common/services/`
- Add types to `common/types/requests.ts` and `responses.ts`
- Generate appropriate hooks (Query or Mutation)
- Use correct import paths (no relative imports)

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
