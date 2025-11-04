---
description: Sync frontend TypeScript types with backend Django serializers
---

Synchronizes types in `common/types/responses.ts` and `common/types/requests.ts` with backend serializers in `../api`.

## Process

### 1. Update Backend & Detect Changes

```bash
cd ../api && git checkout main && git pull origin main && cd -
```

Get last synced commit and current commit:

```bash
LAST_COMMIT=$(python3 .claude/scripts/sync-types-helper.py get-last-commit 2>/dev/null || echo "")
CURRENT_COMMIT=$(cd ../api && git rev-parse HEAD)
```

**First-Time Sync (No LAST_COMMIT):**

If `LAST_COMMIT` is empty, this is a first-time sync. You must:
1. Build the complete api-type-map.json by scanning ALL API endpoints
2. Use the Task tool with subagent_type=Explore to find all API service files in `common/api/`
3. For each endpoint, extract the serializer mappings and build the complete cache
4. Compare ALL frontend types with their backend serializers
5. Update any mismatches found
6. Save the complete cache with all type mappings

**Incremental Sync (Has LAST_COMMIT):**

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

### 2. Identify & Update Affected Types

For each changed serializer file:

**A. Find affected types:**

```bash
python3 .claude/scripts/sync-types-helper.py types-to-sync response FILE ../api
python3 .claude/scripts/sync-types-helper.py types-to-sync request FILE ../api
```

**B. For each affected type:**

1. Read backend serializer fields: `cd ../api && grep -A 30 "class SerializerName" FILE`
2. Read frontend type definition:
   - Response: `grep -A 15 "export type TypeName" common/types/responses.ts`
   - Request: `grep -A 15 "TypeName:" common/types/requests.ts`
3. Compare fields (names, types, required/optional)
4. If mismatch found, use Edit tool to fix frontend type

**C. Update cache:**

```bash
cat << 'EOF' | python3 .claude/scripts/sync-types-helper.py update-metadata
{
  "lastSync": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "lastBackendCommit": "CURRENT_COMMIT_HASH"
}
EOF
```

### 3. Generate Services for New Serializers

**CRITICAL: After adding new types, immediately check if services need to be generated.**

For each NEW serializer (not just updated):

**A. Detect new serializers:**
```bash
cd ../api && git diff ${LAST_COMMIT}..HEAD FILE | grep "^+class.*Serializer"
```

**B. Check if serializer is used in views:**
```bash
cd ../api && grep -r "SerializerName" apps/*/views.py apps/*/urls.py
```

**C. If serializer has an endpoint (found in views/urls):**

1. Extract endpoint details from backend:
   - URL pattern from `urls.py`
   - HTTP method from view decorator/viewset
   - Request/response types already added to `common/types/`

2. **Generate service file immediately** using the same pattern as existing services:
   - Create `common/services/use[TypeName].ts`
   - Follow pattern from `common/services/useManageSubscription.ts` or similar
   - Add proper imports, builder.query for GET, builder.mutation for POST/PUT/DELETE
   - Add cache tags for invalidation
   - Export hook (`useGet[TypeName]Query` or `useCreate[TypeName]Mutation`)
   - Export helper function for non-component usage

3. Update `.claude/api-type-map.json`:
   - Add entry in `response_types` or `request_types`
   - Include `type`, `service`, `endpoint`, `method`, `serializer` fields
   - Update `totalTypes` count

4. Run eslint --fix on new files:
   ```bash
   npx eslint --fix common/services/use[TypeName].ts common/types/responses.ts common/types/requests.ts
   ```

**D. Service Generation Template:**
```typescript
import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const [name]Service = service
  .enhanceEndpoints({ addTagTypes: ['[TagName]'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      get[Name]: builder.query<Res['[key]'], Req['get[Name]']>({
        providesTags: ['[TagName]'],
        query: (q) => ({
          url: `[endpoint-path]`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function get[Name](
  store: any,
  data: Req['get[Name]'],
  options?: Parameters<typeof [name]Service.endpoints.get[Name].initiate>[1],
) {
  return store.dispatch([name]Service.endpoints.get[Name].initiate(data, options))
}
// END OF FUNCTION_EXPORTS

export const {
  useGet[Name]Query,
  // END OF EXPORTS
} = [name]Service
```

### 4. Report Summary

Display:

- Changed serializer files (list)
- Updated response types (count + details)
- Updated request types (count + details)
- **NEW services generated (count + file paths)**
- Total types synced

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

```json
{
  "_metadata": {
    "lastSync": "ISO timestamp",
    "lastBackendCommit": "git hash"
  },
  "response_types": {
    "key": {
      "type": "TypeName",
      "serializer": "apps/path/serializers.py:SerializerName",
      "endpoint": "api/endpoint/",
      "method": "GET"
    }
  },
  "request_types": {
    "key": {
      "type": "TypeName",
      "serializer": "apps/path/serializers.py:SerializerName",
      "endpoint": "api/endpoint/",
      "method": "POST|PUT|PATCH"
    }
  }
}
```

## Notes

- Only sync types with actual Django serializers
- Request types exclude GET/DELETE endpoints (no body validation)
- File uploads (MULTIPART_FORM) need manual verification

## Enum Change Detection

Enum changes require checking beyond serializers:

**When enum definitions change (`apps/*/enums.py`):**
1. Identify which enums changed (e.g., `SubscriptionStatus`, `MailQueueStatus`)
2. Search for TypeScript union types that should match
3. Update the union type with new/removed values

**When model @property methods change (`apps/*/models.py`):**
1. If a `@property` that returns `EnumType.VALUE.name` is modified
2. Check if it now returns a different enum type
3. Update corresponding frontend type's field

**Example:**
```bash
# Detect enum file changes
cd ../api && git diff ${LAST_COMMIT}..HEAD apps/subscriptions/enums.py

# If SubscriptionStatus enum changed:
# 1. Check new enum values
# 2. Update frontend: export type SubscriptionStatus = 'ACTIVE' | 'CANCELLED' | ...
# 3. Find all types using this enum (PartnerSubscription, CompanySummary, etc.)
```
