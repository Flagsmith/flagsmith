---
title: Code References
sidebar_label: Code References
sidebar_position: 30
---

# Code References

Flagsmith Code References provide visibility into where feature flags are evaluated in your codebase. By linking your source code metadata to the Flagsmith dashboard, you can identify stale flags, simplify audits, and safely manage technical debt.

Features list with code reference counts (GitHub badge) next to each flag:

![Features list with code reference badges](/img/code-references-features-list.png)

Code References in the Feature Health tab (open a feature's ⋮ menu → Feature Health → Code References):

![Code References in Feature Health tab](/img/code-references-feature-health.png)

## How it Works

Code References are populated by a scanning tool that identifies flag evaluations within your repository.

1. **CI code scan**: The CI runner searches your repository (`git ls-files`) for feature flag evaluations.
2. **Code references upload**: file path and line number for each evaluation is sent to your Flagsmith project.
3. **Visualisation**: Code references are displayed in Features list, and expanded in Feature detail — look for the "Code References" tab.

:::important Security and Privacy
**Your source code never leaves your CI runner.** Flagsmith does not receive, store, or have access to your source code. Only file paths and line numbers are transmitted to map code references to your dashboard.
:::

# Set up Code References

Code References currently integrates with GitHub, with support for other version control providers planned for future releases.

## GitHub

To authorize the scan, you must first configure your project credentials within your GitHub repository settings under **Settings > Secrets and variables > Actions**.

* **`FLAGSMITH_CODE_REFERENCES_API_KEY` (Secret)**: Generate an Admin API Key in your Flagsmith dashboard under **Organisation Settings > API Keys**.
* **`FLAGSMITH_PROJECT_ID` (Variable)**: This is the integer ID of your project, found in the browser URL when viewing your project: `app.flagsmith.com/project/{ID}/`.

### 1. Simple configuration (Reusable Workflow)

The quickest way to get started is using the Flagsmith reusable workflow. This handles the identification and synchronization of references automatically.

:::note
Note the use of `fromJSON` for the Project ID; GitHub Actions variables are stored as strings, but the Flagsmith API requires an integer.
:::

```yaml
# .github/workflows/flagsmith-code-references.yml
name: Flagsmith Code References

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  collect-code-references:
    name: Collect
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    with:
      flagsmith_project_id: ${{ fromJSON(vars.FLAGSMITH_PROJECT_ID) }}
      flagsmith_admin_api_url: https://api.flagsmith.com/api/v1/ 
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_CODE_REFERENCES_API_KEY }}

```

### 2. Advanced configuration (Individual Actions)

For environments requiring custom logic or specific runner configurations, you can use the discrete actions that compose the workflow.
```yaml
# .github/workflows/flagsmith-code-references.yml
name: Flagsmith Code References

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  collect-code-references:
    name: Collect code references
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      FLAGSMITH_API_URL: https://api.flagsmith.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Fetch feature names
        id: fetch-feature-names
        uses: Flagsmith/ci/.github/actions/fetch-feature-names@main
        with:
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_url: ${{ env.FLAGSMITH_API_URL }}
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_CODE_REFERENCES_API_KEY }}

      - name: Scan code references
        id: scan-code-references
        uses: Flagsmith/ci/.github/actions/scan-code-references@main
        with:
          feature_names: ${{ steps.fetch-feature-names.outputs.feature_names }}

      - name: Upload code references
        uses: Flagsmith/ci/.github/actions/upload-code-references@main
        with:
          code_references: ${{ steps.scan-code-references.outputs.code_references }}
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_url: ${{ env.FLAGSMITH_API_URL }}
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_CODE_REFERENCES_API_KEY }}
          repository_url: ${{ github.server_url }}/${{ github.repository }}
          revision: ${{ github.sha }}


```
## Related Documentation

- [Flagsmith Admin API](/integrating-with-flagsmith/flagsmith-api-overview/admin-api): Learn more about the Admin API used by this integration.
- [GitHub Actions Documentation](https://docs.github.com/en/actions): Official GitHub Actions documentation for workflow configuration.
