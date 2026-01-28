---
title: GitHub Actions Code References
sidebar_label: GitHub Actions Code References
sidebar_position: 1
---

GitHub Actions Code References integration automatically scans your codebase to find exactly where your feature flags are used in your source code. When you open a feature flag in Flagsmith, you'll see a list of all the files and line numbers where that flag is referenced, helping you understand the flag's impact and identify when flags can be safely removed.

The integration runs entirely in your GitHub Actions workflows, ensuring your code never leaves your CI environment. You can configure it to run on a schedule, on push events, on pull requests, on releases, or manually trigger it as needed. The scanning process uses a Docker image that runs locally in your CI runners—your source code stays within your infrastructure, and only reference metadata (file paths, line numbers, and context) is sent to Flagsmith.

## Architecture Overview

The integration uses a reusable GitHub Action workflow to scan your codebase. Here's how it works:

1. **Your repository** triggers a GitHub Actions workflow (via schedule, push, pull request, or release)
2. **Reusable workflow** from `github.com/Flagsmith/ci` (`.github/workflows/collect-code-references.yml`) is invoked
3. **Code scanning** happens locally—composite actions search your repository files for feature flag references using pattern matching
4. **Code references** (file paths, line numbers, and context) are collected and uploaded to the Flagsmith API
5. **Flagsmith dashboard** displays the references in each feature flag's details, showing exactly where each flag is used in your codebase

:::important
**Privacy and Security**: The Docker image runs entirely within your CI runners (GitHub-hosted or self-hosted), ensuring your source code never leaves your infrastructure. Only reference metadata (file paths, line numbers, and context snippets) is sent to Flagsmith—your actual source code is never transmitted.
:::

## Prerequisites

Before you begin, ensure you have:

- A Flagsmith project with feature flags configured
- A Flagsmith Admin API key (found in **Settings** > **API Keys** in your Flagsmith dashboard)
- Access to configure GitHub Actions workflows in your repository
- Your Flagsmith project ID (found in your project's URL: `https://app.flagsmith.com/project/{PROJECT_ID}/...` or in **Project Settings**)

## Setup Options

You can set up code references in two ways:

- **Simple Setup (Reusable Workflow)**: Quickest for most scenarios. Uses a single reusable workflow that handles all steps automatically. Recommended for standard use cases.

- **Advanced Setup (Individual Actions)**: Better for users who need to customize the workflow. Uses granular actions that you compose yourself, giving you full control over each step.

Choose the approach that best fits your needs. Most users should start with the Simple Setup.

## Simple Setup

The quickest way to set up code references is using the reusable workflow from the Flagsmith CI repository (`github.com/Flagsmith/ci`). This approach is recommended for most scenarios as it requires minimal configuration and handles all the steps automatically.

### Step 1: Add Your Secrets

1. Go to your GitHub repository settings.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Add a new repository secret named `FLAGSMITH_ADMIN_API_KEY` with your Flagsmith Admin API key.

### Step 2: Add Your Variables

1. In the same **Secrets and variables** > **Actions** section, go to the **Variables** tab.
2. Add a new repository variable named `FLAGSMITH_PROJECT_ID` with your Flagsmith project ID.

### Step 3: Create the Workflow File

1. Create a new file in your repository at `.github/workflows/flagsmith-code-references.yml`.
2. Add the following workflow configuration:

```yaml
name: Find Flagsmith Code References

on:
  schedule:
    - cron: '0 8 * * *'  # Every day at 8 AM UTC
  workflow_dispatch:  # Allows manual triggering

jobs:
  collect-code-references:
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

### Step 4: Commit and Deploy

1. Commit and push the workflow file to your repository.
2. Go to the **Actions** tab in your GitHub repository.
3. Manually trigger the workflow using the **Run workflow** button, or wait for the scheduled run.
4. Check the workflow logs to confirm it completed successfully.

:::tip
The workflow runs on a daily schedule by default. You can change the `cron` expression or add `push` triggers to run it more frequently.
:::

## What Gets Scanned

The scanner uses regex pattern matching to find feature flag references in your code. It searches for exact matches of your feature flag names as they appear in Flagsmith.

**What gets detected:**
- Feature flag names in code (e.g., `flagsmith.getFlag('my_feature_flag')`)
- Flag names in configuration files
- Flag names in comments (if they match exactly)
- Flag names in strings and documentation

**What gets excluded by default:**
- Build artifacts: `node_modules`, `.git`, `venv`, `.venv`, `__pycache__`, `.tox`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `dist`, `build`, `target`, `out`, `bin`, `obj`
- Framework-specific: `.next`, `.nuxt`, `.cache`
- Test coverage: `coverage`, `htmlcov`, `.nyc_output`

You can customize exclusions using the `exclude_patterns` parameter in your workflow configuration.

## Advanced Setup

For users who need to customize the workflow or have specific requirements, you can use individual GitHub Actions instead of the reusable workflow. This gives you granular control over each step of the process.

### Using Individual Actions

Instead of using the reusable workflow, you can compose your own workflow using individual actions:

```yaml
name: Find Flagsmith Code References

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  collect-code-references:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Fetch feature names
        id: fetch
        uses: Flagsmith/ci/fetch-feature-names@v1.0.0
        with:
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_url: https://api.flagsmith.com/
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}

      - name: Find code references
        id: collect
        uses: Flagsmith/ci/collect-code-references@v1.0.0
        with:
          feature_names: ${{ steps.fetch.outputs.feature_names }}

      - name: Send code references to Flagsmith
        uses: Flagsmith/ci/upload-code-references@v1.0.0
        with:
          code_references: ${{ steps.collect.outputs.code_references }}
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_url: https://api.flagsmith.com/
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
```

This approach allows you to:
- Add custom steps between actions (e.g., filtering, transformation)
- Control the flow and add conditional logic
- Integrate with other CI/CD tools
- Debug individual steps more easily

### Running on Triggers

The reusable workflow supports multiple trigger types for different use cases:

#### Pull Requests

To scan on pull request events:

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

#### Push Events

To scan code on every push to specific branches:

```yaml
on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

#### Releases

To scan on release events:

```yaml
on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

### Using Self-Hosted Runners

The workflow works with both GitHub-hosted and self-hosted runners. To use self-hosted runners, specify the runner label:

```yaml
name: Find Flagsmith Code References

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  collect-code-references:
    runs-on: self-hosted  # Use your self-hosted runner
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

### Using a Custom Flagsmith Instance

If you're using a self-hosted Flagsmith instance, update the API URL:

```yaml
name: Find Flagsmith Code References

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://flagsmith.yourcompany.com/api/v1/
```

## Trigger Types and Use Cases

Choose trigger types based on when and why you want to scan your code:

- **Daily crontab (scheduled)**: Proactively finds references and helps identify stale flags in Flagsmith that may no longer be used in your codebase. Running daily ensures you catch flags that have been removed from code but still exist in Flagsmith.

- **Pull request**: Scans code changes in pull requests to keep code references up-to-date with your development workflow.

- **Release**: Tracks code references at release points, helping you understand which flags were active in each release.

- **Push events**: Keeps references up-to-date as code changes are pushed to your repository. This ensures your code references stay current with the latest code changes.

- **Manual trigger** (`workflow_dispatch`): Allows you to run scans on-demand for testing, immediate updates, or when you need to verify references after making changes.

:::tip
For most use cases, a combination of **daily scheduled scans** (to catch stale flags) and **pull request or push triggers** provides good coverage without excessive CI usage.
:::

## How It Works

The reusable workflow (`collect-code-references.yml` in `Flagsmith/ci`) performs the following steps:

1. **Fetches feature names** from your Flagsmith project using the Admin API
2. **Scans your codebase** for references to feature flag names using regex pattern matching
3. **Collects references** including file paths, line numbers, and code context
4. **Uploads to Flagsmith** via the Admin API endpoint

The scanning process automatically excludes common build artifacts and dependencies (like `node_modules`, `.git`, `venv`, `.cache`, `dist`, `build`, etc.) to focus on your source code.

### Viewing Code References in Flagsmith

In the Flagsmith dashboard, you'll see code references listed under each feature flag's **Code References** tab, showing:
- File paths where the flag is referenced
- Line numbers for each reference  
- Code context snippets

## Verifying Your Setup

After setting up the integration, verify it's working correctly:

1. **Check workflow execution**: Go to your repository's **Actions** tab and verify the workflow runs successfully. Look for logs showing the number of features fetched, files scanned, and references found.

2. **Verify in Flagsmith**: Open a feature flag in Flagsmith that you know is used in your codebase. Navigate to the **Code References** tab and confirm you see the file paths, line numbers, and code snippets where the flag is referenced.

3. **Test with a new flag**: Create a test feature flag, add a reference to it in your code, and trigger a manual workflow run. Verify the reference appears in Flagsmith within a few minutes.

## Next Steps

- View code references in Flagsmith by opening any feature flag and checking the **Code References** tab.
- Use code references to identify unused or stale feature flags that can be safely removed.
- Set up notifications or alerts based on code reference changes to track feature flag usage over time.
- Configure multiple trigger types (e.g., daily schedule + pull requests) for comprehensive coverage.

## Related Documentation

- [Flagsmith Admin API](/integrating-with-flagsmith/flagsmith-api-overview/admin-api): Learn more about the Admin API used by this integration.
- [GitHub Actions Documentation](https://docs.github.com/en/actions): Official GitHub Actions documentation for workflow configuration.
