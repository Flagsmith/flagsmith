# Feature Flags (Flagsmith)

## Overview

The project uses Flagsmith for feature flag management. Flags allow you to control feature visibility without deploying code changes.

**IMPORTANT:** Only implement feature flags when explicitly requested by the user. By default, implement features directly without flags. Feature flags add complexity and should only be used when there's a specific need for:
- Progressive rollouts to specific users
- A/B testing different implementations
- Ability to quickly disable a feature in production
- Gradual feature adoption across user segments

If the user doesn't mention feature flags, implement features directly.

## Project Configuration

Configuration files:
- **Staging**: `common/project.js` (look for `flagsmith` property)
- **Production**: `common/project_prod_*.js` (look for `flagsmith` property)

### Environment-Specific Configuration

See `project-config.local.md` for API keys, project IDs, and environment IDs.

If the file doesn't exist, copy from `project-config.local.md.example` and fill in your values.

## Setup

- **Provider**: `components/FeatureFlagProvider.tsx` wraps the app
- **Configuration**: Flagsmith environment ID in `common/project.ts`
- **User Context**: Flags are user-specific, identified by email

## Usage Pattern

### Standard Pattern (Recommended)

**This project uses `Utils.getFlagsmithHasFeature()` for all feature flag checks.**

```typescript
// In any component (functional or class)
const MyComponent = () => {
  const isFeatureEnabled = Utils.getFlagsmithHasFeature('feature_name')

  return (
    <>
      {isFeatureEnabled && (
        <div>Feature content here</div>
      )}
    </>
  )
}
```

```typescript
// In class components (use in render method)
class MyClassComponent extends Component {
  render() {
    const isFeatureEnabled = Utils.getFlagsmithHasFeature('feature_name')

    return (
      <>
        {isFeatureEnabled && <div>Feature content here</div>}
      </>
    )
  }
}
```

### Alternative: Direct flagsmith Hook (Not Used in This Project)

For reference, the project also supports direct `useFlags` hook, but **Utils.getFlagsmithHasFeature is preferred**:

```typescript
import { useFlags } from 'flagsmith/react'

const MyComponent = () => {
  const flags = useFlags(['feature_name'])
  const isFeatureEnabled = flags.feature_name?.enabled

  return (
    <>
      {isFeatureEnabled && <div>Feature content here</div>}
    </>
  )
}
```

## Best Practices

1. **Use Utils.getFlagsmithHasFeature**: This is the standard pattern used throughout the codebase
2. **Declare flags early in render**: Define flag variables at the top of your render method or component
3. **Conditional rendering**: Wrap new features in flag checks
4. **Table columns**: Hide entire columns when flag is disabled (header + cells)
5. **API calls**: Only make requests if feature flag is enabled
6. **Naming**: Use snake_case for flag names (e.g., `download_invoices`)
7. **For feature values**: Use `Utils.getFlagsmithJSONValue('flag_name', defaultValue)` to get JSON values

## Examples

### Simple Feature Toggle
```typescript
const isNewDashboard = Utils.getFlagsmithHasFeature('new_dashboard')
if (isNewDashboard) {
  return <NewDashboard />
}
return <OldDashboard />
```

### Progressive Feature Rollout Pattern

Common pattern: Add new features behind flags while keeping existing functionality intact.

```typescript
import { useState } from 'react'
import { Tabs } from 'components/base/forms/Tabs'

const MyPage = () => {
  const newFeatureEnabled = Utils.getFlagsmithHasFeature('new_feature')
  const [activeTab, setActiveTab] = useState(0)

  return (
    <div>
      <h2>Section Title</h2>
      {newFeatureEnabled ? (
        <Tabs
          value={activeTab}
          onChange={setActiveTab}
          tabLabels={['Default', 'New Feature']}
        >
          <div><ExistingComponent /></div>
          <div><NewFeatureComponent /></div>
        </Tabs>
      ) : (
        <ExistingComponent />
      )}
    </div>
  )
}
```

### Table Column with Flag
```typescript
const canShowActions = Utils.getFlagsmithHasFeature('show_actions')

return (
  <table>
    <thead>
      <tr>
        <th>Name</th>
        {canShowActions && <th>Actions</th>}
      </tr>
    </thead>
    <tbody>
      {data.map(item => (
        <tr key={item.id}>
          <td>{item.name}</td>
          {canShowActions && (
            <td><Button>Edit</Button></td>
          )}
        </tr>
      ))}
    </tbody>
  </table>
)
```

### Trait Example (User Preferences)
```typescript
// Traits are user-specific preferences, not feature toggles
const flags = useFlags([], ['dark_mode'])
const isDarkMode = flags.dark_mode // Returns boolean/string/number directly

// Setting a trait
const flagsmith = useFlagsmith()
flagsmith.setTrait('dark_mode', true)
```

## Managing Feature Flags via MCP

For MCP tools and workflows, see [mcp-workflows.md](mcp-workflows.md).

## Reference Implementation

See `pages/dashboard.tsx` for a complete example of:
- Feature flag setup with `useFlags(['flag_name'])`
- Conditional component rendering
- Checking `.enabled` property
- Wrapping entire components with feature flags

See `components/DarkModeHandler.tsx` for an example of trait usage.
