---
description: Sync frontend TypeScript types with backend Django serializers
---

Synchronizes types in `common/types/responses.ts` and `common/types/requests.ts` with backend serializers in `../api`.

## Overview

This command runs in **three phases** depending on the current state:

1. **Phase 1 (First-time sync):** Build cache + validate 5-10 critical types (~10k tokens, 2-3 min)
2. **Phase 2 (Full validation):** Validate all remaining types (~50k tokens, 15-20 min)
3. **Phase 3 (Incremental sync):** Only validate types affected by backend changes (~5k-20k tokens)

**Typical workflow:**
```bash
# First run - builds cache and validates critical types
/api-types-sync
# Output: "Phase 1 complete. Run /api-types-sync again for full validation."

# Second run - validates all remaining types for 100% accuracy
/api-types-sync
# Output: "Phase 2 complete. All types now synced with backend."

# Future runs - only sync types affected by backend changes
/api-types-sync
# Output: "Updated 3 types based on backend changes"
```

## How It Works

**Frontend → Backend Mapping:**

Frontend service files (`common/services/use*.ts`) define API calls with type annotations:

```typescript
// Example: common/services/useProject.ts
export const projectService = baseService.injectEndpoints({
  endpoints: (builder) => ({
    getProject: builder.query<Res['project'], { id: string }>({
      query: ({ id }) => `projects/${id}/`,
    }),
    updateProject: builder.mutation<Res['project'], { id: string; data: Req['updateProject'] }>({
      query: ({ id, data }) => ({
        url: `projects/${id}/`,
        method: 'PUT',
        body: data,
      }),
    }),
  }),
})
```

**Mapping process:**
1. Extract: `Res['project']` → endpoint `projects/:id/` → method `GET`
2. Find Django URL: `projects/:id/` → maps to `ProjectViewSet.retrieve`
3. Find serializer: `ProjectViewSet.retrieve` uses `ProjectRetrieveSerializer`
4. Cache mapping: `"response_types.project"` → `"projects/serializers.py:ProjectRetrieveSerializer"`

## Process

### 1. Detect Sync Mode

**IMPORTANT**: This is a monorepo. To get the latest backend changes, merge `main` into your current branch:

```bash
git merge origin/main
```

Get last synced commit and current commit:

```bash
LAST_COMMIT=$(python3 .claude/scripts/sync-types-helper.py get-last-commit 2>/dev/null || echo "")
CURRENT_COMMIT=$(cd ../api && git rev-parse HEAD)
```

Load cache metadata to detect sync mode:

```bash
FULLY_VALIDATED=$(cat .claude/api-type-map.json 2>/dev/null | grep -o '"fullyValidated"[[:space:]]*:[[:space:]]*[a-z]*' | grep -o '[a-z]*$' || echo "false")
```

**Determine which mode:**

- **Phase 1 (First-time sync):** `LAST_COMMIT` is empty → Build cache + validate critical types
- **Phase 2 (Full validation):** `LAST_COMMIT` exists but `FULLY_VALIDATED` is false → Validate all remaining types
- **Phase 3 (Incremental sync):** `LAST_COMMIT` exists and `FULLY_VALIDATED` is true → Check for changed serializers only

---

### Phase 1: First-Time Sync (No LAST_COMMIT)

**Goal:** Build cache and validate critical types to prove system works.

**Steps:**

1. **Scan frontend service files** (`common/services/use*.ts`):
   - Extract all endpoint definitions with `Res['typeName']` and `Req['typeName']`
   - Record endpoint URL and HTTP method for each type

2. **Map types to backend serializers** (multi-step process):
   - For each endpoint URL (e.g., `projects/:id/`):
     - Find matching Django URL pattern in `../api/*/urls.py`
     - Extract the ViewSet or View class name
     - Read the ViewSet/View file to find the serializer class
     - Record: `"serializer": "app/serializers.py:SerializerClassName"`
   - If no serializer found, leave empty string `""`

3. **Build cache structure** (`.claude/api-type-map.json`):
```json
{
  "_metadata": {
    "lastSync": "2025-01-15T10:30:00Z",
    "lastBackendCommit": "abc123...",
    "fullyValidated": false,
    "criticalTypesValidated": ["project", "environment", "organisation", "projectFlag", "identity"]
  },
  "response_types": {
    "project": {
      "type": "project",
      "serializer": "projects/serializers.py:ProjectRetrieveSerializer",
      "endpoint": "projects/:id/",
      "method": "GET"
    }
  },
  "request_types": { ... }
}
```

4. **Validate critical types only** (5-10 types to prove system works):
   - Response types: `project`, `environment`, `organisation`, `projectFlags`/`projectFlag`, `identity`
   - Request types: `updateProject`, `createEnvironment`, `updateOrganisation`, `createProjectFlag`, `createIdentities`
   - For each critical type:
     - Read backend serializer fields
     - Read frontend type definition
     - Compare and fix mismatches
   - Record validated type names in `_metadata.criticalTypesValidated`

5. **Save cache** with `fullyValidated: false` and current commit hash

**Output:** "Phase 1 complete. Cache built with X response types and Y request types. Validated 5-10 critical types. Run `/api-types-sync` again to validate all remaining types."

---

### Phase 2: Full Validation (LAST_COMMIT exists, FULLY_VALIDATED = false)

**Goal:** Validate all remaining types to reach 100% accuracy.

**Steps:**

1. **Load existing cache** and get all types with valid serializers:
```bash
python3 .claude/scripts/sync-types-helper.py syncable-types response > /tmp/response_types.json
python3 .claude/scripts/sync-types-helper.py syncable-types request > /tmp/request_types.json
```

2. **For each syncable type:**
   - Skip if already in `_metadata.criticalTypesValidated` (done in Phase 1)
   - Read backend serializer fields
   - Read frontend type definition
   - Compare and fix mismatches
   - Track progress (e.g., "Validating type 15/96: auditLogs")

3. **Update cache metadata:**
   - Set `fullyValidated: true`
   - Update `lastBackendCommit` to current commit
   - Update `lastSync` timestamp

**Output:** "Phase 2 complete. Validated X response types and Y request types. All types now synced with backend."

---

### Phase 3: Incremental Sync (LAST_COMMIT exists, FULLY_VALIDATED = true)

**Goal:** Validate only types affected by recent backend changes.

**Steps:**

If commits match, report "No changes" and exit.

If commits differ, find changed files:

```bash
cd ../api && git diff ${LAST_COMMIT}..HEAD --name-only | grep -E "(serializers\.py|models\.py|enums\.py)"
```

**File types to check:**

1. **Serializers**: `../api/<app>/serializers.py` - Request/response schemas
2. **Models**: `../api/<app>/models.py` - Data models
3. **Enums**: `../api/<app>/enums.py` - Enum definitions

If no relevant files changed, update cache metadata with new commit and exit.

### 2. Identify & Update Affected Types (Phase 3 only)

For each changed serializer file:

**A. Find affected types using helper script:**

**NOTE:** The helper script only works when cache already exists. For Phase 1 (first-time sync), you must build the cache manually by scanning frontend service files.

```bash
python3 .claude/scripts/sync-types-helper.py types-to-sync response FILE ../api
python3 .claude/scripts/sync-types-helper.py types-to-sync request FILE ../api
```

**B. For each affected type:**

1. **Read backend serializer fields:**
   ```bash
   cd ../api && grep -A 30 "class SerializerName" FILE
   ```
   Extract field names, types, and whether they're required/optional

2. **Read frontend type definition:**
   - Response types: `grep -A 15 "export type TypeName" common/types/responses.ts`
   - Request types: `grep -A 15 "TypeName:" common/types/requests.ts`

3. **Compare fields** (names, types, required/optional)

4. **If mismatch found:** Use Edit tool to fix frontend type

**C. Update cache metadata:**

```bash
cat << 'EOF' | python3 .claude/scripts/sync-types-helper.py update-metadata
{
  "lastSync": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "lastBackendCommit": "CURRENT_COMMIT_HASH"
}
EOF
```

### 3. Report Summary

Display based on phase:

**Phase 1:**
- Cache built: X response types, Y request types
- Critical types validated: [list]
- Next step: Run `/api-types-sync` again for full validation

**Phase 2:**
- Validated: X response types, Y request types
- Types fixed: Z
- All types now synced with backend

**Phase 3:**
- Changed serializer files: [list]
- Updated response types: X (with details)
- Updated request types: Y (with details)
- Total types synced: Z

## Type Comparison Rules

**Field Matching:**

- Ignore URL path parameters (e.g., `company_id`, `id` in path)
- String types → `string`
- Integer/Float types → `number`
- Boolean types → `boolean`
- Optional fields (`required=False`) → append `?` to field name
- Array fields → use `[]` suffix

**Enum Handling:**

- Django CharField with `choices` → TypeScript string union type
- Django enum fields → TypeScript string union type (e.g., `'ACTIVE' | 'CANCELLED' | 'PENDING'`)
- Model `@property` that returns `EnumName.VARIANT.name` → TypeScript string union type
- Example: Backend `status` property returns `SubscriptionStatus.ACTIVE.name` → Frontend should be `status: 'ACTIVE' | 'CANCELLED' | 'NO_PAY' | ...`
- **Note:** Computed properties returning enums require checking the model property definition to extract enum values

**Common Mismatches:**

- Frontend has `string` but backend expects `IntegerField` → change to `number`
- Frontend has required but backend has `required=False` → make optional with `?`
- Frontend includes URL params → remove from type definition
- Frontend includes read-only fields → remove from request types
- Frontend has generic `string` but backend has enum/choices → change to specific union type

## Cache Structure

The cache maps frontend types to their backend serializers for efficient incremental syncing.

**Field Definitions:**

- `"key"`: The type key from `Res['key']` or `Req['key']` in frontend service files
  - Example: `Res['project']` → key is `"project"`
  - Example: `Req['createProject']` → key is `"createProject"`

- `"type"`: Usually matches the key, but can differ for nested types
  - In most cases: `"type": "project"` matches `"key": "project"`

- `"serializer"`: Path to backend serializer in format `"app/serializers.py:ClassName"`
  - Example: `"projects/serializers.py:ProjectRetrieveSerializer"`
  - Empty string `""` if no serializer found (custom responses, view methods)

- `"endpoint"`: The API endpoint URL from frontend service file
  - Example: `"projects/:id/"` (include path params like `:id`)

- `"method"`: HTTP method
  - Response types: `"GET"`, `"POST"`, `"DELETE"` (any method that returns data)
  - Request types: `"POST"`, `"PUT"`, `"PATCH"` (only methods that send body data)

**Example cache:**

```json
{
  "_metadata": {
    "lastSync": "2025-01-15T10:30:00Z",
    "lastBackendCommit": "abc123def456",
    "fullyValidated": false,
    "criticalTypesValidated": ["project", "environment"]
  },
  "response_types": {
    "project": {
      "type": "project",
      "serializer": "projects/serializers.py:ProjectRetrieveSerializer",
      "endpoint": "projects/:id/",
      "method": "GET"
    },
    "projects": {
      "type": "projects",
      "serializer": "projects/serializers.py:ProjectListSerializer",
      "endpoint": "projects/",
      "method": "GET"
    },
    "identityTraits": {
      "type": "identityTraits",
      "serializer": "",
      "endpoint": "/environments/:environmentId/identities/:identity/traits/",
      "method": "GET",
      "note": "Custom response, no serializer"
    }
  },
  "request_types": {
    "createProject": {
      "serializer": "projects/serializers.py:ProjectSerializer",
      "endpoint": "projects/",
      "method": "POST"
    },
    "updateProject": {
      "serializer": "projects/serializers.py:ProjectSerializer",
      "endpoint": "projects/:id/",
      "method": "PUT"
    }
  }
}
```

## Notes

- **Only sync types with actual Django serializers** - Skip custom responses, ChargeBee types, view methods
- **Request types exclude GET/DELETE** - These methods don't send body data, so no request type needed
- **File uploads need manual verification** - MULTIPART_FORM endpoints may not have serializers
- **Helper script requires cache** - `sync-types-helper.py` functions only work after cache is built in Phase 1

## Common Pitfalls

**Pitfall 1: Using helper script during Phase 1**
- ❌ Problem: Running `syncable-types` before cache exists
- ✅ Solution: Build cache manually by scanning frontend service files first

**Pitfall 2: Forgetting path parameters**
- ❌ Problem: Including `:id`, `:projectId` in request/response types
- ✅ Solution: Path params go in the URL, not the request/response body

**Pitfall 3: Assuming type = key**
- ❌ Problem: Using "type" field as cache lookup key
- ✅ Solution: The JSON key (e.g., `"project"`) is the lookup key, `"type"` field is metadata

**Pitfall 4: Stopping after Phase 1**
- ❌ Problem: Only critical types validated, 80%+ of types unchecked
- ✅ Solution: Run `/api-types-sync` again for Phase 2 full validation

**Pitfall 5: Skipping enum type updates**
- ❌ Problem: Frontend has `status: string`, backend changed to enum
- ✅ Solution: Check serializer for `choices` and model for `@property` methods

## Enum Change Detection

Enum changes require checking beyond serializers:

**When enum definitions change (`*/enums.py`):**

Django enum changes often don't show up in serializer diffs. You must:

1. **Detect enum file changes:**
   ```bash
   cd ../api && git diff ${LAST_COMMIT}..HEAD --name-only | grep enums.py
   ```

2. **For each changed enum:**
   - Read the new enum values
   - Search for TypeScript types using this enum
   - Update the union type

**Example:**
```python
# Backend: subscriptions/enums.py
class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PENDING = "pending"  # NEW VALUE ADDED
```

```typescript
// Frontend: common/types/responses.ts (BEFORE)
export type SubscriptionStatus = 'ACTIVE' | 'CANCELLED'

// Frontend: common/types/responses.ts (AFTER)
export type SubscriptionStatus = 'ACTIVE' | 'CANCELLED' | 'PENDING'
```

**When model @property methods change (`*/models.py`):**

If a `@property` returns `EnumType.VALUE.name`, it serializes as a string union:

```python
# Backend: subscriptions/models.py
class Subscription(models.Model):
    @property
    def status(self):
        return SubscriptionStatus.ACTIVE.name  # Returns 'ACTIVE' (string)
```

Frontend type should be:
```typescript
status: 'ACTIVE' | 'CANCELLED' | 'PENDING'  // NOT string
```

**Detection process:**
1. Find changed model files with `@property` methods
2. Check if property returns `EnumType.VALUE.name`
3. Find all types with this field
4. Update to string union type
