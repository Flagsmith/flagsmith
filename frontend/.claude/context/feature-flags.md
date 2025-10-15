# Feature Flags (Dogfooding Flagsmith)

## Overview

**Important**: This codebase IS Flagsmith itself - the feature flag platform. The frontend uses the Flagsmith JavaScript SDK internally for "dogfooding" (using our own product to control feature releases).

## Default Project Context

**ALWAYS use the Flagsmith Website project unless the user explicitly specifies a different project.**

When working with feature flags, releases, or any feature flag operations:
- Default project: "Flagsmith Website"
- Only use a different project if the user explicitly mentions it by name or ID

## Configuration

- **Flagsmith SDK**: Imported as `flagsmith` npm package
- **Environment ID**: `4vfqhypYjcPoGGu8ByrBaj` (configured in `common/project.js`)
- **API Endpoint**: `https://edge.api.flagsmith.com/api/v1/`
- **Self-hosted**: Points to own API backend in `../api/`
- Uses Flagsmith to control its own feature rollouts

### Flagsmith Organization Details
- **Organization ID**: 13 (Flagsmith)
- **Main Project ID**: 12 (Flagsmith Website)
- **Main Project Name**: "Flagsmith Website"

### Environments

| Environment | ID | API Key | Description |
|-------------|-----|---------|-------------|
| **Production** | 22 | `4vfqhypYjcPoGGu8ByrBaj` | Live production environment (default in `common/project.js`) |
| **Staging** | 1848 | `ENktaJnfLVbLifybz34JmX` | Staging/testing environment |
| **Demo** | 20524 | `Ueo6zkrS8kt4LzuaJF9NFJ` | Demo environment |
| **Self hosted defaults** | 21938 | `MXSepNNQEacBBzxAU7RagJ` | Defaults for self-hosted instances |
| **Demo2** | 59277 | `DarXioFcqTNy53CeyvsqP4` | Second demo environment |

## Querying Feature Flags by Environment

To quickly check feature flag values for any environment:

```bash
# Production flags
curl -H "X-Environment-Key: 4vfqhypYjcPoGGu8ByrBaj" \
  "https://edge.api.flagsmith.com/api/v1/flags/" | grep -A 5 "flag_name"

# Staging flags
curl -H "X-Environment-Key: ENktaJnfLVbLifybz34JmX" \
  "https://edge.api.flagsmith.com/api/v1/flags/" | grep -A 5 "flag_name"

# Get all flags (no filter)
curl -H "X-Environment-Key: 4vfqhypYjcPoGGu8ByrBaj" \
  "https://edge.api.flagsmith.com/api/v1/flags/"
```

**Note**: The frontend in `common/project.js` is configured to use **Production** (`4vfqhypYjcPoGGu8ByrBaj`) by default.

## Usage Pattern

The Flagsmith frontend uses utility methods to access feature flags:

```typescript
// Check if feature is enabled
Utils.getFlagsmithHasFeature('feature_name')

// Get feature value
Utils.getFlagsmithValue('feature_name')

// Get JSON feature value with default
Utils.getFlagsmithJSONValue('feature_name', defaultValue)
```

See `common/utils/utils.ts` for implementation details.

## Common Patterns in Feature Flag Platforms

When building feature flag UI components, you'll typically work with:

### Feature States
- Features have states per environment
- Each state has: `enabled` (boolean), `feature_state_value` (string/number/json)

### Segments
- Target specific user groups with feature variations
- Segment overrides apply before default feature states

### Identities
- Individual user overrides
- Highest priority in evaluation

### Example API Structures

```typescript
// Feature
{
  id: number
  name: string
  type: 'FLAG' | 'MULTIVARIATE' | 'CONFIG'
  project: number
  default_enabled: boolean
  description: string
}

// Feature State
{
  id: number
  enabled: boolean
  feature: number
  environment: number
  feature_state_value: string | null
}

// Segment
{
  id: number
  name: string
  rules: SegmentRule[]
  project: number
}
```

## Working with Feature Flag Components

When building UI for feature management:

1. **Feature List**: Display all features for a project
2. **Environment Toggle**: Enable/disable features per environment
3. **Value Editor**: Set configuration values for features
4. **Segment Overrides**: Target specific user segments
5. **Identity Overrides**: Override for specific users
6. **Audit Log**: Track all feature flag changes

## Reference Examples

Look at these existing components for patterns:
- Search for components with "Feature" in the name: `find web/components -name "*Feature*"`
- Environment management: `find web/components -name "*Environment*"`
- Segment components: `find web/components -name "*Segment*"`

## Best Practices

1. **Environment-specific**: Features are scoped to environments
2. **Audit everything**: Track all feature flag changes for compliance
3. **Gradual rollouts**: Use segments for percentage-based rollouts
4. **Identity targeting**: Test features with specific users first
5. **Change requests**: Require approval for production flag changes (if enabled)
