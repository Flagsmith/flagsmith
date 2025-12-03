# API Integration Guide

## Overview

This project uses **RTK Query** (Redux Toolkit Query) for all API calls. The workflow is optimized for type safety and automatic sync with backend Django serializers.

**Finding Backend Endpoints**: See `.claude/context/backend-integration.md` for strategies to locate and understand backend API endpoints.

## Quick Start: Adding a New Endpoint (Complete Example)

This example shows how to add a new endpoint for fetching company invoices (a real implementation from the codebase).

### Step 1: Find Backend Endpoint

Use strategies from `backend-integration.md` to locate the endpoint.

**Backend endpoint found:** `GET /organisations/{organisation_id}/invoices`

### Step 2: Add Request Type

**File:** `common/types/requests.ts`

```typescript
export type Req = {
  // ... existing types
  getCompanyInvoices: {
    organisation_id: string
  }
}
```

### Step 3: Add RTK Query Endpoint

**File:** `common/services/useInvoice.ts`

```typescript
export const invoiceService = service
  .enhanceEndpoints({ addTagTypes: ['Invoice'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      // Add new endpoint
      getCompanyInvoices: builder.query<
        Res['invoices'],
        Req['getCompanyInvoices']
      >({
        providesTags: [{ id: 'LIST', type: 'Invoice' }],
        query: (req) => ({
          url: `organisations/${organisation_id}/invoices`,
        }),
        transformResponse(res: InvoiceSummary[]) {
          return res?.map((v) => ({ ...v, date: v.date * 1000 }))
        },
      }),
    }),
  })

export const {
  useGetCompanyInvoicesQuery, // Export new hook
  // END OF EXPORTS
} = invoiceService
```

### Step 4: Use in Component

```typescript
import { useGetCompanyInvoicesQuery } from 'common/services/useInvoice'

const MyComponent = () => {
  const { subscriptionDetail } = useDefaultSubscription()
  const companyId = subscriptionDetail?.company_id

  const { data: invoices, error, isLoading } = useGetCompanyInvoicesQuery(
    { organisation_id: `${companyId}` },
    { skip: !organisation_id } // Skip if no company ID
  )

  if (isLoading) return <Loader />
  if (error) return <ErrorMessage>{error}</ErrorMessage>

  return (
    <div>
      {invoices?.map(inv => <div key={inv.id}>{inv.id}</div>)}
    </div>
  )
}
```

### Step 5: Run Linter

```bash
npx eslint --fix common/types/requests.ts common/services/useInvoice.ts
```

**Done!** The endpoint is now integrated and ready to use.

## Manual Service Creation (Rare Cases)

If you need to manually create a service (follow template in `.claude/commands/api.md`):

1. **Identify backend endpoint**
    - Use `/backend <search-term>` to search backend codebase
    - Check `../api/apps/*/serializers.py`, `../api/apps/*/views.py`, `apps/*/urls.py`
    - Or swagger docs: https://api.flagsmith.com/api/v1/docs/

2. **Define types** in `common/types/`
    - Response: `export type EntityName = { field: type }` in `responses.ts`
    - Add to `Res` type: `entityName: EntityName`
    - Request: `getEntityName: { param: type }` in `requests.ts`

3. **Create service** `common/services/use{Entity}.ts`
    - Use `builder.query` for GET, `builder.mutation` for POST/PUT/DELETE
    - Configure cache tags: `providesTags`, `invalidatesTags`
    - Export hooks: `useGetEntityQuery`, `useCreateEntityMutation`

4. **Register in type map** `.claude/api-type-map.json`
    - Add to `response_types` or `request_types` with full metadata
    - Increment `_metadata.totalTypes`

5. **Run linter**
    ```bash
    npx eslint --fix common/services/use*.ts common/types/*.ts
    ```

### Backend → Frontend Type Mapping

| Django Type | TypeScript |
|------------|------------|
| `CharField` | `string` |
| `IntegerField` | `number` |
| `BooleanField` | `boolean` |
| `DateTimeField` | `string` (ISO) |
| `required=False` | `field?: type` |
| `many=True` | `Type[]` |
| Enum/Choices | `'A' \| 'B'` |

### Example Service Structure

```typescript
import { service } from 'common/service'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'

export const entityService = service
  .enhanceEndpoints({ addTagTypes: ['Entity'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getEntity: builder.query<Res['entity'], Req['getEntity']>({
        providesTags: (res) => [{ id: res?.id, type: 'Entity' }],
        query: (query) => ({
          url: `entities/${query.id}`,
        }),
      }),
      updateEntity: builder.mutation<Res['entity'], Req['updateEntity']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Entity' },
          { id: res?.id, type: 'Entity' },
        ],
        query: (query) => ({
          body: query,
          method: 'PUT',
          url: `entities/${query.id}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useGetEntityQuery,
  useUpdateEntityMutation,
  // END OF EXPORTS
} = entityService
```

See `common/services/useAuditLog.ts` for a complete example.

## State Management

- **Redux Toolkit + RTK Query** for all API calls
- Store: `common/store.ts` with redux-persist
- Base service: `common/service.ts`
  The `npx ssg` CLI requires interactive input that cannot be automated. Instead, **manually create RTK Query services** following the patterns in existing service files.
- **IMPORTANT**: When implementing API logic, prefer implementing it in the RTK Query service layer (using `transformResponse`, `transformErrorResponse`, etc.) rather than in components. This makes the logic reusable across the application.

## Error Handling Patterns

### RTK Query Mutations

```typescript
const [createMail, { isLoading, error }] = useCreateMailMutation()

const handleSubmit = async () => {
  try {
    const result = await createThing(data).unwrap()
    toast('Success!')
  } catch (err) {
    if ('status' in err) {
      // FetchBaseQueryError - has status, data, error
      const errMsg = 'error' in err ? err.error : JSON.stringify(err.data)
      toast.error(errMsg)
    } else {
      // SerializedError - has message, code, name
        toast(err.message || 'An error occurred', 'danger')
        toast(err.message || 'An error occurred')
    }
  }
}
```

### RTK Query Queries

```typescript
const { data, error, isLoading, refetch } = useThing({ id: '123' })

// Display error in UI, it won't render if error is undefined
return <ErrorMessage>{error}</ErrorMessage>

// Retry on error
const handleRetry = () => refetch()
```
