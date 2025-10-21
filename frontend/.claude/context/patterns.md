# Common Code Patterns

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

## Web Component Patterns

This codebase is primarily web-focused (React + Webpack).

### Modals

Use the modal system from `components/base/Modal`:

```typescript
import { openModal, openConfirm } from 'components/base/Modal'

// Open a custom modal
openModal('Modal Title', <ModalContent />)

// Open a confirmation dialog
openConfirm(
  'Confirm Action',
  'Are you sure?',
  async (closeModal) => {
    // Perform action
    closeModal()
  }
)
```

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

Check existing components for pagination patterns. The codebase may use custom pagination logic or libraries like react-virtualized.

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
import { entityService } from 'common/services/useEntity'

export const clearEntityCache = () => {
  getStore().dispatch(
    entityService.util.invalidateTags([{ type: 'Entity', id: 'LIST' }])
  )
}
```

### Automatic Invalidation

Cache invalidation is handled automatically through RTK Query tags:

```typescript
// Mutation invalidates the list
createEntity: builder.mutation<Res['entity'], Req['createEntity']>({
  invalidatesTags: [{ type: 'Entity', id: 'LIST' }],
  // This will automatically refetch any active queries with matching tags
}),
```

## Type Organization

### Request and Response Types

All API types go in `common/types/`:

```typescript
// common/types/requests.ts
export type Req = {
  getEntity: {
    id: string
  }
  createEntity: {
    name: string
  }
  // END OF TYPES
}

// common/types/responses.ts
export type Res = {
  entity: Entity
  entities: Entity[]
  // END OF TYPES
}
```

### Shared Types

**Shared types:**

Types used across multiple request/response types should be defined separately and imported.

## SSG CLI Usage (Optional)

You can use `npx ssg` to generate new API services:

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

**Note**: Manual service creation is also acceptable - follow patterns from existing services.

## Linting

Always run ESLint on files you modify:

```bash
npx eslint --fix <file>
```

Or run it on all files:

```bash
npm run lint:fix
```
