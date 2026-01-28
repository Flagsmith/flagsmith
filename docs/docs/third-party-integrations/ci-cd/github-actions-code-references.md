---
title: GitHub Actions Code References
sidebar_label: GitHub Actions Code References
sidebar_position: 1
---

# Code References

Flagsmith Code References provide visibility into flag usage by scanning your codebase in CI and displaying the results in your dashboard. This helps you identify stale flags and safely manage technical debt.

## How it Works

The integration uses a GitHub Action to scan your code for feature flag keys.

1. **Local Scan**: The runner searches your repository for flag keys using pattern matching.
2. **Metadata Sync**: File paths, line numbers, and context snippets are sent to the Flagsmith Admin API.
3. **Visualization**: References appear in the **Code References** tab of each feature flag.

:::info Security
Your source code **never leaves your runner**. Only the metadata and a few lines of code surrounding the flag are sent to Flagsmith.
:::

## Prerequisites

* **Flagsmith Admin API Key**: Found in **Settings > API Keys**.
* **Project ID**: Found in **Project Settings**.
* Write access to your GitHub repository.

## Setup

### 1. Add Secrets and Variables

In your GitHub repository, navigate to **Settings > Secrets and variables > Actions** and add:

* `FLAGSMITH_ADMIN_API_KEY` (Secret)
* `FLAGSMITH_PROJECT_ID` (Variable)

### 2. Create the Workflow

Add `.github/workflows/flagsmith-sync.yml` to your repository:

```yaml
name: Flagsmith Code References

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  sync:
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}

```

:::caution Why no Pull Request triggers?
This workflow syncs the current state of your code to the dashboard. Running it on Pull Requests will overwrite your dashboard with unmerged code references. Only run this on your default branch.
:::

## Advanced Usage

### Individual Actions

For custom logic or specific runner requirements, you can use the discrete actions:

```yaml
jobs:
  custom-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Flagsmith/ci/fetch-feature-names@v1.0.0
        id: fetch
        with:
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
      - uses: Flagsmith/ci/collect-code-references@v1.0.0
        id: collect
        with:
          feature_names: ${{ steps.fetch.outputs.feature_names }}
      - uses: Flagsmith/ci/upload-code-references@v1.0.0
        with:
          code_references: ${{ steps.collect.outputs.code_references }}
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}

```

### Self-Hosted Flagsmith

If you are self-hosting Flagsmith, provide your API URL in the `with` block:

```yaml
with:
  flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
  flagsmith_admin_api_url: https://your-api-url.com/api/v1/

```

### Exclusions

The scanner automatically ignores common directories like `node_modules`, `dist`, `.git`, and `bin`.

## Related Documentation

- [Flagsmith Admin API](/integrating-with-flagsmith/flagsmith-api-overview/admin-api): Learn more about the Admin API used by this integration.
- [GitHub Actions Documentation](https://docs.github.com/en/actions): Official GitHub Actions documentation for workflow configuration.
