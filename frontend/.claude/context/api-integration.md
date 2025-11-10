# API Integration Guide

## Overview

This project uses **RTK Query** (Redux Toolkit Query) for all API calls. The workflow is optimized for type safety and automatic sync with backend Django serializers.

## Quick Start: Adding a New Endpoint (Complete Example)

This example shows how to add a new endpoint for fetching company invoices (a real implementation from the codebase).

### Step 1: Check Backend API

```bash
cd ../api
git fetch
git log --oneline origin/feat/your-branch -n 10
git show COMMIT_HASH:apps/customers/urls.py | grep -A 5 "invoice"
git show COMMIT_HASH:apps/customers/views.py | grep -A 20 "def get_company_invoices"
```

**Backend endpoint found:** `GET /customers/companies/{company_id}/invoices`

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
          url: `customers/companies/${req.company_id}/invoices`,
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
    { company_id: `${companyId}` },
    { skip: !companyId } // Skip if no company ID
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

## Primary Workflow: Automatic via `/api-types-sync`

**ALWAYS start with `/api-types-sync`** when working with APIs. This command:
1. Pulls latest backend changes from `../api`
2. Detects new/changed Django serializers
3. Updates TypeScript types in `common/types/`
4. **Automatically generates RTK Query services** for new endpoints
5. Updates `.claude/api-type-map.json` for tracking

### When `/api-types-sync` Auto-Generates Services

The command detects:
- New serializer classes in `apps/*/serializers.py`
- Associated views/endpoints in `apps/*/views.py` and `apps/*/urls.py`
- Creates complete service files with proper RTK Query patterns
- Registers everything in the type map

### When to Manually Use `/api`

Only use the `/api` command when:
- Creating a service for an existing backend endpoint that was missed
- `/api-types-sync` didn't auto-generate (rare edge case)
- Implementing a frontend-only service (non-backend endpoint)

**In 95% of cases, `/api-types-sync` handles service generation automatically.**

## Manual Service Creation (Rare Cases)

If you need to manually create a service (follow template in `.claude/commands/api.md`):

1. **Identify backend endpoint**
    - Use `/backend <search-term>` to search backend codebase
    - Check `apps/*/serializers.py`, `apps/*/views.py`, `apps/*/urls.py`
    - Or swagger docs: https://staging-api.hoxtonmix.com/api/v3/docs/

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

## Type Sync Architecture

### `.claude/api-type-map.json`

Cache file mapping frontend → backend for type sync:

```json
{
  "_metadata": {
    "lastBackendCommit": "a73427688...",
    "totalTypes": 48
  },
  "response_types": {
    "entityName": {
      "type": "EntityType",
      "service": "common/services/useEntity.ts",
      "endpoint": "entities/{id}",
      "method": "GET",
      "serializer": "apps/entities/serializers.py:EntitySerializer"
    }
  }
}
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

## Finding Backend Endpoints

### Quick Reference - Common Customer Portal API Patterns

**Base URL Pattern**: `/api/v3/` (varies by resource)

| Resource | List | Detail | Actions |
|----------|------|--------|---------|
| **Mail** | `GET /mailbox/mails` | `GET /mailbox/mails/{id}` | `POST /mailbox/mails/{id}/scan`, `POST /mailbox/mails/{id}/forward` |
| **Offers** | `GET /offers/` | `GET /offers/{id}/` | N/A |
| **Account** | `GET /account` | N/A | N/A |
| **KYC** | `GET /kyc/steps` | `GET /kyc/status` | `POST /kyc/verify`, `GET /kyc/link` |
| **Subscriptions** | N/A | `GET /customers/companies/{id}/hosted-page` | N/A |
| **Addresses** | N/A | N/A | `POST /addresses`, `PATCH /addresses/{id}` |
| **Payment** | N/A | N/A | `POST /topup`, `POST /payment-sources` |

### Search Strategy

1. **Use `/backend` slash command**: `/backend <search-term>` searches backend codebase
2. **Check URL patterns**: Look in `../api/apps/<resource>/urls.py`
    - Common apps: `mailbox`, `customers`, `kyc`, `offers`, `subscriptions`, `checkout`
3. **Check ViewSets**: Look in `../api/apps/<resource>/views.py`
4. **Common file download pattern**:
    - Backend returns PDF/file with `Content-Disposition: attachment; filename=...`
    - Use `responseHandler` in RTK Query to handle blob downloads
    - See `common/services/useMailDownload.ts` for example

### File Download Pattern

**Use the reusable utility function:**

```typescript
import { handleFileDownload } from 'common/utils/fileDownload'

query: (query) => ({
  url: `resource/${query.id}/pdf`,
  responseHandler: (response) => handleFileDownload(response, 'invoice.pdf'),
})
```

The utility automatically:
- Extracts filename from `Content-Disposition` header
- Creates and triggers download
- Cleans up blob URLs
- Returns `{ data: { url } }` format

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
    const result = await createMail(data).unwrap()
    toast.success('Success!')
  } catch (err) {
    if ('status' in err) {
      // FetchBaseQueryError - has status, data, error
      const errMsg = 'error' in err ? err.error : JSON.stringify(err.data)
      toast.error(errMsg)
    } else {
      // SerializedError - has message, code, name
      toast.error(err.message || 'An error occurred')
    }
  }
}
```

### RTK Query Queries

```typescript
const { data, error, isLoading, refetch } = useGetMailQuery({ id: '123' })

// Display error in UI
if (error) {
  return <ErrorMessage error={error} />
}

// Retry on error
const handleRetry = () => refetch()
```

### 401 Unauthorized Handling

**Automatic logout on 401** is handled in `common/service.ts`:
- All 401 responses (except email confirmation) trigger logout
- Debounced to prevent multiple logout calls
- Uses the logout endpoint from the service

### Backend Error Response Format

Backend typically returns:
```json
{
  "detail": "Error message here",
  "code": "ERROR_CODE"
}
```

Access in error handling:
```typescript
if ('data' in err && err.data?.detail) {
  toast.error(err.data.detail)
}
```

## Cross-Platform Pattern

- Web (`/project/api.ts`) and Mobile (`/mobile/app/api.ts`) implement same interface from `common/api-common.ts`
- Example: `getApi().loginRedirect()` uses Next.js Router on web, React Native Navigation on mobile
