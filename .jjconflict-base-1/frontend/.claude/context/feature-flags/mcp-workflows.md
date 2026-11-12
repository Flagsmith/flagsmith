# Flagsmith MCP Workflows

This project uses the **flagsmith-admin-api MCP** for feature flag management. All operations are performed through MCP tools instead of manual API calls or web console.

## ⚠️ CRITICAL: Project Verification Before Creating Flags

**STOP! Before creating ANY feature flag, follow this mandatory checklist:**

1. ✅ **Verify the correct project**: Check `project-config.local.md` for the correct project ID
2. ✅ **Read configuration**: Check `common/project.js` to see the Flagsmith API key
3. ✅ **Confirm with MCP**: Run `mcp__flagsmith__list_project_environments` with the project_id from config to verify
4. ✅ **Create ONCE**: Only call `mcp__flagsmith__create_feature` ONCE with the correct project_id

**NEVER:**
- ❌ Create flags in multiple projects to "try" which one is correct
- ❌ Guess the project ID without verification
- ❌ Create duplicate flags

**Why this matters:** Creating flags in the wrong project pollutes other Flagsmith projects with incorrect flags that don't belong there. This is a critical error.

## Known Limitations

**IMPORTANT:** Published feature versions cannot be modified via the Flagsmith API.

- After creating a flag with MCP (`mcp__flagsmith__create_feature`), the flag is created but disabled by default
- To enable/disable the flag in specific environments, you must use the Flagsmith web UI at https://app.flagsmith.com
- This is a Flagsmith API limitation, not a tooling issue
- The MCP can create flags, but enabling/disabling must be done manually via the UI

**Workflow:**
1. Create flag via MCP → ✅ Automated
2. Implement code with `useFlags()` → ✅ Automated
3. Enable flag in staging/production → ❌ Manual (via Flagsmith UI)

When documenting completion, always inform the user that step 3 requires manual action via the web UI.

## CRITICAL: When User Says "Create a Feature Flag"

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

## Standard Workflow Example

```
User: "Add a download button, create this under a feature flag download_invoices"

Step 1: Create flag in Flagsmith
  - Use mcp__flagsmith__list_organizations (if needed)
  - Use mcp__flagsmith__list_projects_in_organization (find project)
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

## Available MCP Tools

The MCP provides tools prefixed with `mcp__flagsmith-admin-api__` for managing feature flags.

### Discovery & Listing
- **`list_organizations`** - List all organizations accessible with your API key
- **`list_projects_in_organization`** - List all projects in an organization
- **`list_project_features`** - List all feature flags in a project
- **`list_project_environments`** - List all environments (staging, production, etc.)
- **`list_project_segments`** - List user segments for targeting

### Feature Flag Operations
- **`create_feature`** - Create a new feature flag (defaults to disabled)
- **`get_feature`** - Get detailed information about a specific flag
- **`update_feature`** - Update flag name or description
- **`get_feature_evaluation_data`** - Get analytics/metrics for a flag
- **`get_feature_external_resources`** - Get linked resources (Jira, GitHub, etc.)
- **`get_feature_code_references`** - Get code usage information

### Feature State Management
- **`get_environment_feature_versions`** - Get version info for a flag in an environment
- **`get_environment_feature_version_states`** - Get state info for a specific version
- **`create_environment_feature_version_state`** - Create new state (enable/disable/set value)
- **`update_environment_feature_version_state`** - Update existing state
- **`patch_environment_feature_version_state`** - Partially update state

### Advanced Features
- **`create_multivariate_option`** - Create A/B test variants
- **`list_multivariate_options`** - List all variants for a flag
- **`update_multivariate_option`** / **`delete_multivariate_option`** - Manage variants
- **`create_project_segment`** - Create user targeting rules
- **`update_project_segment`** / **`get_project_segment`** - Manage segments
- **`list_project_change_requests`** - List change requests for approval workflows
- **`create_environment_change_request`** - Create controlled deployment requests
- **`list_project_release_pipelines`** - List automated deployment pipelines

## Common Workflows

### 1. Find Your Project
```
Step 1: List organizations
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_organizations

Step 2: List projects in your organization
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_projects_in_organization
Parameters: {"org_id": <ORG_ID_FROM_STEP_1>}

Step 3: Find project by matching repository name to project name
```

### 2. List Existing Feature Flags
```
Tool: mcp__flagsmith-admin-api__flagsmith_admin_api_list_project_features
Parameters: {"project_id": <PROJECT_ID>}
Optional: Add query params for pagination: {"page": 1, "page_size": 50}
```

### 3. Create a New Feature Flag
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

### 4. Enable/Disable a Flag in an Environment
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

## Best Practices

1. **Always look up IDs dynamically** - Don't hardcode organization, project, or feature IDs
2. **Match repository to project** - Project names typically correspond to repository names
3. **Start disabled** - New flags are created disabled by default
4. **Enable in staging first** - Test in non-production environments before enabling in production
5. **Use descriptive names** - Follow snake_case naming: `download_invoices`, `new_dashboard`
6. **Document usage** - Note which components use each flag

## Environment-Specific Configuration

When creating a new feature flag:
1. **Create the flag** (disabled globally by default)
2. **Enable for staging/development** to allow testing
3. **Keep production disabled** until ready for release
4. **Use change requests** for production changes if approval workflows are configured
