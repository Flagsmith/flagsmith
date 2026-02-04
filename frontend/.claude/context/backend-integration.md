# Backend Integration Guide

## Backend Repository Structure

The backend API is located at `../api` (sibling directory to this frontend repo).

### Key Backend Directories

```
../api/
├── apps/
│   ├── projects/         # Projects and features
│   ├── environments/     # Environment management
│   ├── features/         # Feature flags
│   ├── segments/         # User segments
│   ├── organisations/    # Organization management
│   ├── users/           # User management
│   ├── permissions/     # Access control
│   └── audit/          # Audit logs
└── tests/              # Test files mirror apps/ structure
```

## Finding Backend Endpoints

### Method 1: Search by Feature Branch

When a feature is on a specific branch:

```bash
cd ../api
git fetch
git log --oneline origin/feat/your-branch -n 10
```

Look for the relevant commit, then examine the changes:

```bash
# See what files were changed
git show COMMIT_HASH --stat

# View specific file at that commit
git show COMMIT_HASH:apps/customers/urls.py

# Search for specific pattern in file
git show COMMIT_HASH:apps/customers/urls.py | grep -A 5 "invoice"
git show COMMIT_HASH:apps/customers/views.py | grep -A 20 "def get_company_invoices"
```

### Method 2: Search Current Codebase

If the feature is already merged or on main:

```bash
cd ../api

# Search for URL patterns
grep -r "path.*features" apps/*/urls.py

# Search for view functions
grep -r "def get.*feature" apps/*/views.py

# Search for serializers
grep -r "class.*FeatureSerializer" apps/*/serializers.py
```

### Method 3: Use `/backend` Command

From the frontend, use the `/backend` slash command:

```
/backend feature endpoint
```

This searches the backend codebase for relevant code.

## Understanding Backend Code

### 1. URL Patterns (`urls.py`)

Django URL patterns define the API routes:

```python
# apps/features/urls.py
path(
    "<int:feature_id>",
    get_feature,
    name="feature-detail",
),
```

**Maps to:** `GET /api/v1/features/{feature_id}`

### 2. View Functions (`views.py`)

Views handle the HTTP request/response:

```python
# apps/features/views.py
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_feature(request, feature_id, *args, **kwargs):
    feature = Feature.objects.get(id=feature_id)
    serializer = FeatureSerializer(feature)
    return Response(status=status.HTTP_200_OK, data=serializer.data)
```

Key things to note:
- HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- Authentication required: Usually JWT or Token based
- Permissions: `@permission_classes`
- Path parameters: `feature_id` from URL
- Return format: Usually `Response(data=...)`

### 3. Service Layer (`services.py`)

Business logic is in service classes:

```python
# apps/features/services.py (if exists)
# Note: Flagsmith backend may not always use a service layer
# Business logic often lives directly in views or models
```

### 4. Serializers (`serializers.py`)

Serializers define the data structure:

```python
# apps/features/serializers.py
class FeatureSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    type = serializers.CharField()
    default_enabled = serializers.BooleanField()
    created_date = serializers.DateTimeField()
```

## API Response Patterns

### List Endpoints

```
GET /api/v3/resource/
Response: [{ id: 1, ... }, { id: 2, ... }]
```

### Detail Endpoints

```
GET /api/v3/resource/{id}/
Response: { id: 1, name: "...", ... }
```

### Nested Resources

```
GET /api/v3/admin/partners/{partner_id}/customers
Response: [{ id: 1, name: "...", ... }, { id: 2, name: "...", ... }]
```

### Action Endpoints

```
POST /api/v3/admin/partners/{id}/activate
Body: { commission_rate: 10.5 }
Response: { success: true, partner: {...} }
```

## Common Partner Portal Endpoints

| Resource | Endpoint | Method | Notes |
|----------|----------|--------|-------|
| **Partners** | `/admin/partners` | GET | List all partners |
| | `/admin/partners/{id}` | GET | Partner detail |
| | `/admin/partners/{id}` | PUT/PATCH | Update partner |
| | `/admin/partners/{id}/activate` | POST | Activate partner |
| | `/admin/partners/{id}/deactivate` | POST | Deactivate partner |
| **Customers** | `/admin/partners/{id}/customers` | GET | List partner's customers |
| | `/admin/customers/{id}` | GET | Customer detail |
| **Commissions** | `/admin/partners/{id}/commissions` | GET | Partner commission history |
| | `/admin/commissions/{id}` | GET | Commission detail |
| **Payouts** | `/admin/partners/{id}/payouts` | GET | Partner payout history |
| | `/admin/payouts/{id}` | GET | Payout detail |
| | `/admin/payouts` | POST | Create new payout |
| **Offers** | `/offers` | GET | List available offers |
| | `/offers/{id}` | GET | Offer detail |
| **Dashboard** | `/admin/partners/{id}/stats` | GET | Partner statistics/metrics |

## Testing Backend Changes Locally

### 1. Run Backend Locally

```bash
cd ../api
# Follow backend README for setup
python manage.py runserver
```

### 2. Point Frontend to Local Backend

```bash
# In frontend repo
API_URL=http://localhost:8000/api/v3/ npm run dev
```

### 3. Check API Response

```bash
# Test endpoint directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v3/admin/partners/123
```

## Common Patterns

### Permission Checks

Backend often checks:
- `@permission_classes([IsAuthenticated])` - Must be logged in
- `@permission_classes([IsAdminUser])` - Admin user required
- `@has_partner_permission([PartnerPermissionType.VIEW_CUSTOMERS])` - Specific permission required

Frontend should mirror these checks using:
```typescript
const { user } = useAuth()
const isAdmin = user?.is_admin
const canViewCustomers = user?.permissions?.includes('VIEW_CUSTOMERS')
```

### Pagination

Backend may return paginated responses:
```json
{
  "count": 100,
  "next": "https://api.../resource/?page=2",
  "previous": null,
  "results": [...]
}
```

Frontend should handle with:
```typescript
query: (req) => ({
  url: `resource`,
  params: { page: req.page, page_size: 20 }
})
```

### Error Responses

Backend typically returns:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

Frontend should extract `detail` for user-facing error messages.

## Checklist for New Endpoints

- [ ] Find endpoint in backend code (views.py, urls.py)
- [ ] Note HTTP method (GET, POST, etc.)
- [ ] Note path parameters (`{id}`, `{company_id}`)
- [ ] Note query parameters (`?page=1`)
- [ ] Check authentication requirements
- [ ] Check permission requirements
- [ ] Find or create matching serializer for response type
- [ ] Check if response needs transformation (e.g., timestamps)
- [ ] Test endpoint directly with curl or Postman
- [ ] Add request type to `common/types/requests.ts`
- [ ] Add/extend RTK Query service in `common/services/`
- [ ] Use hook in component with loading/error handling
- [ ] Run linter on modified files
