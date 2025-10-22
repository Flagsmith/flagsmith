# API Type Synchronization

Frontend TypeScript types in `common/types/responses.ts` mirror backend Django serializers from `../api`.

## Type Mapping (Django → TypeScript)

| Django Serializer                            | TypeScript Type                                |
| -------------------------------------------- | ---------------------------------------------- |
| `CharField()`                                | `field: string`                                |
| `CharField(required=False)`                  | `field?: string`                               |
| `CharField(allow_null=True)`                 | `field: string \| null`                        |
| `CharField(required=False, allow_null=True)` | `field?: string \| null`                       |
| `CharField(choices=EnumType.choices)`        | `field: 'VALUE1' \| 'VALUE2' \| 'VALUE3'`      |
| `IntegerField()` / `FloatField()`            | `field: number`                                |
| `BooleanField()`                             | `field: boolean`                               |
| `DateTimeField()` / `DateField()`            | `field: string` (ISO format)                   |
| `ImageField()` / `MediaSerializer()`         | `field: Image` where `Image = { url: string }` |
| `ListField` / `many=True`                    | `Type[]`                                       |
| `JSONField`                                  | `Record<string, any>` or specific interface    |
| `SerializerMethodField()`                    | Usually optional: `field?: type`               |
| Nested serializer                            | Nested type/interface                          |

### Enum Types

Django enums serialize as strings and should map to TypeScript string union types:

**Direct enum fields:**
```python
# Backend
class MySerializer(serializers.ModelSerializer):
    status = serializers.CharField(choices=StatusType.choices)
```
```typescript
// Frontend
status: 'ACTIVE' | 'PENDING' | 'CANCELLED'
```

**Computed properties returning enums:**
```python
# Backend Model
@property
def status(self) -> str:
    return SubscriptionStatus.ACTIVE.name  # Returns "ACTIVE"
```
```typescript
// Frontend - check model to find enum values
status: 'ACTIVE' | 'CANCELLED' | 'NO_PAY' | 'NO_ID' | 'PENDING_CANCELLATION'
```

**Important:** When a serializer field comes from a model `@property`, you must:
1. Find the property definition in the model file
2. Identify which enum it returns (e.g., `SubscriptionStatus.VARIANT.name`)
3. Look up the enum definition to get all possible values
4. Map to TypeScript union type with all enum values

## Frontend-Only Types

Types marked with `//claude-ignore` in `responses.ts` are frontend-only and should not be synced:

```typescript
export type Res = {
  // Backend-synced types above this line

  //claude-ignore - Frontend-only state
  redirect: Url
  devSettings: DevSettings
  userData: UserData
}
```

Frontend-computed fields should be preserved with comment:

```typescript
expired: boolean //FE-computed
currentPage: number //FE-computed
```

## Cache System

The `.claude/api-type-map.json` file maps frontend types to backend serializers and tracks enum dependencies:

```json
{
  "_metadata": {
    "description": "Maps frontend API endpoints to backend Django serializers for type synchronization",
    "lastSync": "2025-10-17T13:38:50Z",
    "lastBackendCommit": "af60d9e3eef4696ca04dfd8010b4e89aa70cbe89",
    "enum_dependencies": {
      "description": "Maps TypeScript union types to Django enums for change detection",
      "mappings": {
        "SubscriptionStatus": {
          "typescript_type": "SubscriptionStatus",
          "django_enum": "apps/subscriptions/enums.py:SubscriptionStatus",
          "used_in_types": ["PartnerSubscription", "Subscription", "Company"]
        }
      }
    }
  },
  "response_types": {
    "offer": {
      "type": "Offer",
      "service": "common/services/useOffers.ts",
      "endpoint": "offers/{id}/",
      "method": "GET",
      "serializer": "apps/offers/serializers.py:OfferDetailsSerializer"
    }
  }
}
```

This cache enables:

- **Instant lookup of serializer locations** - Find backend serializer for any frontend type
- **Enum dependency tracking** - Know which Django enums map to TypeScript union types
- **Cross-reference type usage** - See which response types use each enum
- **Change detection** - Identify which types need updates when enums change
- **Backend commit tracking** - Know which backend version was last synced

## Common Patterns

**Nested types:**

- `Image` → `{ url: string }`
- `Address` → Import from `requests.ts`
- Paged responses → Generic wrapper with `count`, `next?`, `previous?`, `results[]`

**Finding serializers:**

1. Check cache first (`.claude/api-type-map.json`)
2. Search service files: `grep -r ": TypeName" common/services/`
3. Search backend: `grep -r "SerializerName" ../api/*/views.py`

**Before syncing:**
Always merge main into the branch to update backend code to its latest version

## Enum Dependency Tracking

The `_metadata.enum_dependencies` section tracks the relationship between Django enums and TypeScript union types:

**Structure:**
```json
{
  "SubscriptionStatus": {
    "typescript_type": "SubscriptionStatus",
    "django_enum": "apps/subscriptions/enums.py:SubscriptionStatus",
    "used_in_types": ["PartnerSubscription", "Subscription", "Company"]
  }
}
```

**What it tracks:**
- **typescript_type** - Name of the TypeScript union type in `responses.ts`
- **django_enum** - Backend file path and enum class name
- **used_in_types** - List of response types that use this enum

**How to use it:**

1. **Find all enums used in the project:**
   ```bash
   # Read the enum_dependencies section
   cat .claude/api-type-map.json | jq '._metadata.enum_dependencies.mappings'
   ```

2. **Check which types use a specific enum:**
   ```typescript
   // Example: Find types using SubscriptionStatus
   // Look at used_in_types: ["PartnerSubscription", "Subscription", "Company"]
   ```

3. **Locate the Django enum definition:**
   ```bash
   # Use the django_enum path
   cat ../api/subscriptions/enums.py | grep -A 10 "class SubscriptionStatus"
   ```

4. **Update all affected types when enum changes:**
   ```bash
   # If SubscriptionStatus changes, update all types in used_in_types array
   # Each type listed needs to be checked and synced
   ```

## Monitoring Enum Changes

Enum changes require additional tracking:

**Files to monitor:**
- `apps/*/enums.py` - Enum value changes
- `apps/*/models.py` - Property methods returning enums
- `apps/*/serializers.py` - Serializer field changes

**When to update frontend:**
- New enum value added → Add to TypeScript union
- Enum value removed → Remove from TypeScript union (check usage first!)
- Model `@property` changes which enum it returns → Update field type

**Example workflow using enum dependencies:**
```bash
# 1. Check what changed since last sync
git diff LAST_COMMIT..HEAD --name-only | grep -E "(enums|models|serializers)\.py"

# 2. If subscriptions/enums.py changed, check the api-type-map.json:
cat .claude/api-type-map.json | jq '._metadata.enum_dependencies.mappings.SubscriptionStatus'

# 3. Read the updated enum values:
cat ../api/subscriptions/enums.py | grep -A 10 "class SubscriptionStatus"

# 4. Update the TypeScript union type in common/types/responses.ts
# 5. Check all types listed in used_in_types to ensure they're still correct
```

**Automated enum sync workflow:**
When the `/api-types-sync` command runs, it:
1. Reads all enum dependencies from the cache
2. Checks if Django enum files have changed since last sync
3. Re-reads enum values from backend
4. Updates TypeScript union types
5. Verifies all types in `used_in_types` still use the correct enum
