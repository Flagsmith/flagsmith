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
import useInfiniteScroll from 'common/useInfiniteScroll'
import { useGetFeaturesQuery } from 'common/services/useFeature'

const FeatureList = ({ projectId }: Props) => {
  const {
    data,
    isLoading,
    isFetching,
    loadMore,
    refresh,
    searchItems,
  } = useInfiniteScroll(
    useGetFeaturesQuery,
    { projectId, page_size: 20 },
  )

  return (
    <div>
      {data?.results?.map(feature => (
        <FeatureRow key={feature.id} {...feature} />
      ))}
      {data?.next && (
        <Button onClick={loadMore} disabled={isFetching}>
          Load More
        </Button>
      )}
    </div>
  )
}
```

## Error Handling

### RTK Query Error Pattern

```typescript
const [createFeature, { isLoading, error }] = useCreateFeatureMutation()

const handleSubmit = async () => {
  try {
    const result = await createFeature(data).unwrap()
    // Success - result contains the response
    toast('Feature created successfully')
  } catch (err) {
    // Error handling
    if ('status' in err) {
      // FetchBaseQueryError
      const errMsg = 'error' in err ? err.error : JSON.stringify(err.data)
      toast(errMsg, 'danger')
    } else {
      // SerializedError
      toast(err.message || 'An error occurred', 'danger')
    }
  }
}
```

### Query Refetching

```typescript
const { data, refetch } = useGetFeatureQuery({ id: '123' })

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
import { featureService } from 'common/services/useFeature'

export const clearFeatureCache = () => {
  getStore().dispatch(
    featureService.util.invalidateTags([{ type: 'Feature', id: 'LIST' }])
  )
}
```

### Automatic Invalidation

Cache invalidation is handled automatically through RTK Query tags:

```typescript
// Mutation invalidates the list
createFeature: builder.mutation<Res['feature'], Req['createFeature']>({
  invalidatesTags: [{ type: 'Feature', id: 'LIST' }],
  // This will automatically refetch any active queries with matching tags
}),
```

## Type Organization

### Request and Response Types

All API types go in `common/types/`:

```typescript
// common/types/requests.ts
export type Req = {
  getFeatures: PagedRequest<{
    project: number
    q?: string
  }>
  createFeature: {
    project: number
    name: string
    type: 'FLAG' | 'CONFIG'
  }
  // END OF TYPES
}

// common/types/responses.ts
export type Res = {
  features: PagedResponse<Feature>
  feature: Feature
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
