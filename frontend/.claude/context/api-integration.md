# API Integration Guide

## Workflow

### Preferred: Manual Service Creation

The `npx ssg` CLI requires interactive input that cannot be automated. Instead, **manually create RTK Query services** following the patterns in existing service files.

1. **Check backend code** in `../api` for endpoint details
    - Search backend directly using Grep or Glob tools
    - Common locations: `*/views.py`, `*/urls.py`, `*/serializers.py`
    - Check API documentation or Swagger UI if available in your environment

2. **Define types** in `common/types/requests.ts` and `responses.ts`
    - Add to `Req` type for request parameters
    - Add to `Res` type for response data
    - Match backend serializer field names and types

3. **Create service file** in `common/services/use{Entity}.ts`
    - Follow pattern from existing services (e.g., `usePartner.ts`, `useCompany.ts`)
    - Use `service.enhanceEndpoints()` and `.injectEndpoints()`
    - Define queries with `builder.query<Res['entity'], Req['getEntity']>()`
    - Define mutations with `builder.mutation<Res['entity'], Req['createEntity']>()`
    - Set appropriate `providesTags` and `invalidatesTags` for cache management
    - Export hooks: `useGetEntityQuery`, `useCreateEntityMutation`, etc.

4. **CRITICAL: Update `.claude/api-type-map.json`** to register the new endpoint
    - Add entry in `request_types` section with:
      - `type`: TypeScript type signature (e.g., `{id: string, name: string}`)
      - `serializer`: Backend serializer path (e.g., `entities/serializers.py:EntitySerializer`)
      - `endpoint`: API endpoint pattern (e.g., `/api/v1/entities/{id}/`)
      - `method`: HTTP method (GET, POST, PUT, DELETE)
      - `service`: Frontend service file path (e.g., `common/services/useEntity.ts`)
    - Add entry in `response_types` section (if needed)
    - This enables the `/api-types-sync` command to track type changes

5. **Verify implementation**
    - Check URL matches backend endpoint exactly
    - Verify HTTP method (GET, POST, PUT, DELETE)
    - Ensure request body structure matches backend serializer
    - Test with actual API calls

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

### Search Strategy

1. **Search backend directly**: Use Grep/Glob tools to search the `../api` directory
2. **Check URL patterns**: Look in `../api/*/urls.py`
3. **Check ViewSets**: Look in `../api/*/views.py`
4. **Common file download pattern**:
    - Backend returns PDF/file with `Content-Disposition: attachment; filename=...`
    - Use `responseHandler` in RTK Query to handle blob downloads
    - Check existing service files for examples

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
- **Use `npx ssg` CLI to generate new services** (optional but helpful)
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
- Check the service.ts file for specific 401 handling logic
- Typically debounced to prevent multiple logout calls

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

## Platform Patterns

- Web and common code are separated in the directory structure
- Check existing patterns in the codebase for platform-specific implementations
