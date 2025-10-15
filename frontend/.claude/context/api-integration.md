# API Integration Guide

## Workflow

**ALWAYS use the `npx ssg` CLI for API integration**

1. Check backend code in `../api/` Django backend for endpoint details
   - Use the `/backend` slash command to search backend: `/backend <search-term>`
   - Common Django apps: `organisations/`, `projects/`, `environments/`, `features/`, `users/`, `segments/`
   - Check: `<app>/views.py`, `<app>/urls.py`, `<app>/serializers.py`
2. Run `npx ssg` and follow prompts to generate RTK Query service
3. Define types in `common/types/requests.ts` and `responses.ts`
4. Match URLs with backend endpoints in RTK Query config
5. Use generated hooks: `useGetXQuery()`, `useCreateXMutation()`

## Finding Backend Endpoints

### Quick Reference - Common Flagsmith API Patterns

**Base URL Pattern**: `/api/v1/` (Flagsmith API v1)

| Resource | List | Detail | Common Actions |
|----------|------|--------|----------------|
| **Projects** | `GET /projects/` | `GET /projects/{id}/` | `POST /projects/`, `PUT /projects/{id}/` |
| **Environments** | `GET /environments/` | `GET /environments/{api_key}/` | `POST /environments/`, `PUT /environments/{id}/` |
| **Features** | `GET /features/` | `GET /features/{id}/` | `POST /features/`, `PUT /features/{id}/`, `DELETE /features/{id}/` |
| **Feature States** | `GET /features/{id}/featurestates/` | `GET /featurestates/{id}/` | `POST /featurestates/`, `PUT /featurestates/{id}/` |
| **Identities** | `GET /identities/` | `GET /identities/{id}/` | `POST /identities/`, `DELETE /identities/{id}/` |
| **Segments** | `GET /segments/` | `GET /segments/{id}/` | `POST /segments/`, `PUT /segments/{id}/`, `DELETE /segments/{id}/` |
| **Users** | `GET /users/` | `GET /users/{id}/` | `POST /users/`, `PUT /users/{id}/` |
| **Organisations** | `GET /organisations/` | `GET /organisations/{id}/` | `POST /organisations/`, `PUT /organisations/{id}/` |

### Search Strategy

1. **Use `/backend` slash command**: `/backend <search-term>` searches Django codebase
2. **Check URL patterns**: Look in `../api/<app>/urls.py`
   - Main API router: `../api/app/urls.py`
3. **Check ViewSets/Views**: Look in `../api/<app>/views.py`
4. **Check Serializers**: Look in `../api/<app>/serializers.py` for request/response schemas

### Pagination Pattern

Flagsmith API uses cursor-based pagination:

```typescript
// Backend returns:
{
  results: [...],
  next: "cursor_string",
  previous: "cursor_string",
  count: 100
}

// Use with useInfiniteScroll hook
import useInfiniteScroll from 'common/useInfiniteScroll'

const { data, loadMore, isLoading } = useInfiniteScroll(
  useGetFeaturesQuery,
  { projectId: '123', page_size: 20 }
)
```

## State Management

- **Redux Toolkit + RTK Query** for all API calls
- Store: `common/store.ts` with redux-persist
- Base service: `common/service.ts`
- **ALWAYS use `npx ssg` CLI to generate new services**

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
