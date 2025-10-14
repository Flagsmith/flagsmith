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
- **Environment ID**: Configured in `common/project.js`
- **Self-hosted**: Points to own API backend in `../api/`
- Uses Flagsmith to control its own feature rollouts

## Usage Pattern

**NOTE**: This codebase does NOT use `useFlags` hook. Check the actual implementation in the codebase for the correct pattern.

The Flagsmith frontend likely uses one of these patterns:
1. Global `flagsmith` instance accessed directly
2. Custom provider/context for feature flags
3. Direct API calls to feature states

To find the correct pattern, search for:
```bash
grep -r "flagsmith" common/ web/ --include="*.ts" --include="*.tsx" --include="*.js"
```

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
