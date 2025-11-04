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

To find your organization and project IDs, use the MCP tools (see "Managing Feature Flags" section below).

## Setup

- **Provider**: `components/FeatureFlagProvider.tsx` wraps the app
- **Configuration**: Flagsmith environment ID in `common/project.ts`
- **User Context**: Flags are user-specific, identified by email

## Usage Pattern

```typescript
import { useFlags } from 'flagsmith/react'

const MyComponent = () => {
  // Request specific FEATURES by name (first parameter)
  const flags = useFlags(['feature_name'])
  const isFeatureEnabled = flags.feature_name?.enabled

  // For TRAITS, use the second parameter
  // const flags = useFlags([], ['trait_name'])
  // const traitValue = flags.trait_name

  return (
    <>
      {isFeatureEnabled && (
        <div>Feature content here</div>
      )}
    </>
  )
}
```

## Best Practices

1. **Features vs Traits**:
    - **Features** (first parameter): `useFlags(['feature_name'])` - Returns `{ enabled: boolean, value: any }`
    - **Traits** (second parameter): `useFlags([], ['trait_name'])` - Returns raw value (string/number/boolean)
2. **Always check `.enabled` for features**: Use `flags.flag_name?.enabled` to get boolean
3. **Conditional rendering**: Wrap new features in flag checks
4. **Table columns**: Hide entire columns when flag is disabled (header + cells)
5. **API calls**: Only make requests if feature flag is enabled
6. **Naming**: Use snake_case for flag names (e.g., `download_invoices`)

## Examples

### Simple Feature Toggle
```typescript
const flags = useFlags(['new_dashboard'])
if (flags.new_dashboard?.enabled) {
  return <NewDashboard />
}
return <OldDashboard />
```

### Progressive Feature Rollout Pattern

Common pattern: Add new features behind flags while keeping existing functionality intact.

```typescript
import { useState } from 'react'
import { useFlags } from 'flagsmith/react'
import { Tabs } from 'components/base/forms/Tabs'

const MyPage = () => {
  const { new_feature } = useFlags(['new_feature'])
  const [activeTab, setActiveTab] = useState(0)

  // Without flag: show only existing component
  // With flag: show tabs with existing + new component
  return (
    <div>
      <h2>Section Title</h2>
      {new_feature?.enabled ? (
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

**Benefits:**
- Zero risk to existing users when flag is off
- Easy A/B testing by enabling for specific users
- Can roll back instantly by disabling flag
- Clean removal path once feature is validated

### Table Column with Flag
```typescript
const flags = useFlags(['show_actions'])
const canShowActions = flags.show_actions?.enabled

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

### Button with Flag
```typescript
const flags = useFlags(['allow_delete'])
const canDelete = flags.allow_delete?.enabled

return (
  <>
    {canDelete && (
    <Button onClick={handleDelete}>Delete</Button>
  )}
</>
)
```

## Managing Feature Flags via MCP

This project uses the **flagsmith-admin-api MCP** for feature flag management. All operations are performed through MCP tools instead of manual API calls or web console.

### CRITICAL: When User Says "Create a Feature Flag"

**When the user requests to create a feature flag, you MUST:**

1. ✅ **Actually create the flag in Flagsmith** using `mcp__flagsmith__create_feature`
2. ✅ **Implement the frontend code** that uses the flag with `useFlags()`
3. ✅ **Return the flag details** (ID, name, project) to confirm creation

**DO NOT:**
- ❌ Only implement the code without creating the flag
- ❌ Assume the flag already exists
- ❌ Assume the user will create it manually

**This is a two-part task:**
- **Backend (Flagsmith)**: Create the flag entity in Flagsmith
- **Frontend (Code)**: Write code that checks the flag with `useFlags()`

Both parts are required when "create a feature flag" is requested.

**Standard Workflow Example:**
```
User: "Add a download button, create this under a feature flag download_invoices"

Step 1: Create flag in Flagsmith
  - Use mcp__flagsmith__list_organizations (if needed)
  - Use mcp__flagsmith__list_projects_in_organization (find "portal" project)
  - Use mcp__flagsmith__create_feature with name "download_invoices"
  - Confirm flag ID and status to user

Step 2: Implement code
  - Add useFlags(['download_invoices']) to component
  - Wrap button with flag check: {flags.download_invoices?.enabled && <Button>Download</Button>}
  - Test that code compiles

Step 3: Report completion
  - Confirm flag created in Flagsmith (with ID)
  - Confirm code implementation complete
```

### Available MCP Tools

The MCP provides tools prefixed with `mcp__flagsmith-admin-api__` for managing feature flags. Key operations:

#### Discovery & Listing
- **`list_organizations`** - List all organizations accessible with your API key
- **`list_projects_in_organization`** - List all projects in an organization
- **`list_project_features`** - List all feature flags in a project
- **`list_project_environments`** - List all environments (staging, production, etc.)
- **`list_project_segments`** - List user segments for targeting

#### Feature Flag Operations
- **`create_feature`** - Create a new feature flag (defaults to disabled)
- **`get_feature`** - Get detailed information about a specific flag
- **`update_feature`** - Update flag name or description
- **`get_feature_evaluation_data`** - Get analytics/metrics for a flag
- **`get_feature_external_resources`** - Get linked resources (Jira, GitHub, etc.)
- **`get_feature_code_references`** - Get code usage information

#### Feature State Management
- **`get_environment_feature_versions`** - Get version info for a flag in an environment
- **`get_environment_feature_version_states`** - Get state info for a specific version
- **`create_environment_feature_version_state`** - Create new state (enable/disable/set value)
- **`update_environment_feature_version_state`** - Update existing state
- **`patch_environment_feature_version_state`** - Partially update state

#### Advanced Features
- **`create_multivariate_option`** - Create A/B test variants
- **`list_multivariate_options`** - List all variants for a flag
- **`update_multivariate_option`** / **`delete_multivariate_option`** - Manage variants
- **`create_project_segment`** - Create user targeting rules
- **`update_project_segment`** / **`get_project_segment`** - Manage segments
- **`list_project_change_requests`** - List change requests for approval workflows
- **`create_environment_change_reques...`** - Create controlled deployment requests
- **`list_project_release_pipelines`** - List automated deployment pipelines

### Common Workflows

#### 1. Find Your Project
```
Step 1: List organizations
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_organizations

Step 2: List projects in your organization
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_projects_in_organization
Parameters: {"org_id": <ORG_ID_FROM_STEP_1>}

Step 3: Find project by matching repository name to project name
```

#### 2. List Existing Feature Flags
```
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_project_features
Parameters: {"project_id": <PROJECT_ID>}
Optional: Add query params for pagination: {"page": 1, "page_size": 50}
```

#### 3. Create a New Feature Flag
```
Step 1: Create the flag (disabled by default)
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_create_feature
Parameters:
  pathParameters: {"project_id": <PROJECT_ID>}
  body: {"name": "flag_name", "description": "Description"}

Step 2: Get environment IDs
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_project_environments
Parameters: {"project_id": <PROJECT_ID>}

Step 3: Enable for staging/development
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_get_environment_feature_versions
Then use create/update_environment_feature_version_state to enable
```

#### 4. Enable/Disable a Flag in an Environment
```
Step 1: Get feature versions
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_get_environment_feature_versions
Parameters: {"environment_id": <ENV_ID>, "feature_id": <FEATURE_ID>}

Step 2: Update feature state
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_patch_environment_feature_version_state
Parameters:
  pathParameters: {"environment_id": <ENV_ID>, "feature_id": <FEATURE_ID>, "version_id": <VERSION_ID>}
  body: {"enabled": true}
```

### Best Practices

1. **Always look up IDs dynamically** - Don't hardcode organization, project, or feature IDs
2. **Match repository to project** - Project names typically correspond to repository names
3. **Start disabled** - New flags are created disabled by default
4. **Enable in staging first** - Test in non-production environments before enabling in production
5. **Use descriptive names** - Follow snake_case naming: `download_invoices`, `new_dashboard`
6. **Document usage** - Note which components use each flag

### Environment-Specific Configuration

When creating a new feature flag:
1. **Create the flag** (disabled globally by default)
2. **Enable for staging/development** to allow testing
3. **Keep production disabled** until ready for release
4. **Use change requests** for production changes if approval workflows are configured

### Trait Example (User Preferences)
```typescript
// Traits are user-specific preferences, not feature toggles
const flags = useFlags([], ['dark_mode'])
const isDarkMode = flags.dark_mode // Returns boolean/string/number directly

// Setting a trait
const flagsmith = useFlagsmith()
flagsmith.setTrait('dark_mode', true)
```

## Reference Implementation

See `pages/dashboard.tsx` for a complete example of:
- Feature flag setup with `useFlags(['flag_name'])`
- Conditional component rendering
- Checking `.enabled` property
- Wrapping entire components with feature flags

See `components/DarkModeHandler.tsx` for an example of trait usage.
