---
title: GitHub Actions Code References
sidebar_label: GitHub Actions Code References
sidebar_position: 1
---

GitHub Actions Code References integration automatically scans your codebase to find exactly where your feature flags are used in your source code. When you open a feature flag in Flagsmith, you'll see a list of all the files and line numbers where that flag is referenced, helping you understand the flag's impact and identify when flags can be safely removed.

The integration runs entirely in your GitHub Actions workflows, ensuring your code never leaves your CI environment. You can configure it to run on a schedule, on push events, on pull requests, on releases, or manually trigger it as needed. The scanning process uses a Docker image that runs locally in your CI runners—your source code stays within your infrastructure, and only reference metadata (file paths, line numbers, and context) is sent to Flagsmith.

## Architecture Overview

The integration uses a reusable GitHub Action workflow that runs a Docker image to scan your codebase. Here's how it works:

1. **Your repository** triggers a GitHub Actions workflow (via schedule, push, pull request, or release)
2. **Reusable workflow** from `github.com/Flagsmith/ci-tools` (`.github/workflows/collect-code-references.yml`) is invoked
3. **Docker image** (`flagsmith-find-code-references`) is pulled and executed in your CI environment
4. **Code scanning** happens locally—the Docker image searches your repository files for feature flag references using pattern matching
5. **Code references** (file paths, line numbers, and context) are collected and uploaded to the Flagsmith API
6. **Flagsmith dashboard** displays the references in each feature flag's details, showing exactly where each flag is used in your codebase

:::important
**Privacy and Security**: The Docker image runs entirely within your CI runners (GitHub-hosted or self-hosted), ensuring your source code never leaves your infrastructure. Only reference metadata (file paths, line numbers, and context snippets) is sent to Flagsmith—your actual source code is never transmitted.
:::

## Prerequisites

Before you begin, ensure you have:

- A Flagsmith project with feature flags configured
- A Flagsmith Admin API key with permissions to create code references (found in **Settings** > **API Keys** in your Flagsmith dashboard)
- Access to configure GitHub Actions workflows in your repository
- Your Flagsmith project ID (found in your project's URL: `https://app.flagsmith.com/project/{PROJECT_ID}/...` or in **Project Settings**)

## Setup Options

You can set up code references in two ways:

- **Simple Setup (Reusable Workflow)**: Quickest for most scenarios. Uses a single reusable workflow that handles all steps automatically. Recommended for standard use cases.

- **Advanced Setup (Individual Actions)**: Better for users who need to customize the workflow. Uses granular actions that you compose yourself, giving you full control over each step.

Choose the approach that best fits your needs. Most users should start with the Simple Setup.

## Simple Setup

The quickest way to set up code references is using the reusable workflow from the Flagsmith CI tools repository (`github.com/Flagsmith/ci-tools`). This approach is recommended for most scenarios as it requires minimal configuration and handles all the steps automatically.

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
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

### Step 4: Verify the Setup

1. Commit and push the workflow file to your repository.
2. Go to the **Actions** tab in your GitHub repository.
3. Manually trigger the workflow using the **Run workflow** button, or wait for the scheduled run.
4. Check the workflow logs to confirm it completed successfully. You should see:
   - "Fetching feature names from Flagsmith"
   - "Scanning codebase for references"
   - "Found X references for Y features"
   - "Uploading code references to Flagsmith"
5. In Flagsmith, open any feature flag and navigate to the **Code References** tab to see the files and line numbers where the flag is used.

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
        uses: Flagsmith/ci-tools/fetch-feature-names@v1.0.0
        with:
          flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
          flagsmith_admin_api_url: https://api.flagsmith.com/
          flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}

      - name: Find code references
        id: collect
        uses: Flagsmith/ci-tools/collect-code-references@v1.0.0
        with:
          feature_names: ${{ steps.fetch.outputs.feature_names }}
          exclude_patterns: ".git,node_modules,vendor,venv"

      - name: Send code references to Flagsmith
        uses: Flagsmith/ci-tools/upload-code-references@v1.0.0
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

### Customizing the Scan (Reusable Workflow)

When using the reusable workflow, you can exclude specific files or directories from scanning:

```yaml
name: Find Flagsmith Code References

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
      exclude_patterns: ".git,node_modules,vendor,venv,custom-folder"
```

### Running on Pull Requests

Pull request tracking can notify you when references are removed, helping you catch flag removals before they're merged:

```yaml
name: Find Flagsmith Code References

on:
  pull_request:
    branches:
      - main
      - develop
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

### Running on Push Events

To scan code on every push to specific branches:

```yaml
name: Find Flagsmith Code References

on:
  push:
    branches:
      - main
      - develop
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://api.flagsmith.com/
```

### Running on Releases

Release tracking can notify you when a reference is gone, helping identify flags that may have been removed in a release:

```yaml
name: Find Flagsmith Code References

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  collect-code-references:
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
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
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
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
    uses: Flagsmith/ci-tools/.github/workflows/collect-code-references.yml@v1.0.0
    secrets:
      flagsmith_admin_api_key: ${{ secrets.FLAGSMITH_ADMIN_API_KEY }}
    with:
      flagsmith_project_id: ${{ vars.FLAGSMITH_PROJECT_ID }}
      flagsmith_admin_api_url: https://flagsmith.yourcompany.com/api/v1/
```

## Trigger Types and Use Cases

Choose trigger types based on when and why you want to scan your code:

- **Daily crontab (scheduled)**: Proactively finds references and helps identify stale flags in Flagsmith that may no longer be used in your codebase. Running daily ensures you catch flags that have been removed from code but still exist in Flagsmith.

- **Pull request**: Notifies you when references are removed in PRs, helping you catch flag removals before they're merged. This allows you to review and clean up flags as part of your code review process.

- **Release**: Tracks when references disappear in releases, helping you identify flags that may have been removed during a release cycle. Release tracking can notify you when a reference is gone, making it easier to identify flags that were removed in a specific release.

- **Push events**: Keeps references up-to-date as code changes are pushed to your repository. This ensures your code references stay current with the latest code changes.

- **Manual trigger** (`workflow_dispatch`): Allows you to run scans on-demand for testing, immediate updates, or when you need to verify references after making changes.

:::tip
For most use cases, a combination of **daily scheduled scans** (to catch stale flags) and **pull request triggers** (to catch removals during code review) provides good coverage without excessive CI usage.
:::

## How It Works

The reusable workflow (`collect-code-references.yml` in `Flagsmith/ci-tools`) performs the following steps:

1. **Fetches feature names**: Retrieves all feature flag names from your Flagsmith project using the Admin API. This provides the list of flags to search for in your codebase.

2. **Pulls Docker image**: Downloads the `flagsmith-find-code-references` Docker image from the container registry. This image contains the scanning logic and runs entirely in your CI environment.

3. **Scans your codebase**: The Docker image searches through your repository files for references to feature flag names using regex pattern matching. It processes files in your repository, looking for exact matches of feature flag names.

4. **Collects references**: For each match found, the scanner gathers:
   - File path (relative to repository root)
   - Line number where the flag is referenced
   - Code context around the reference

5. **Uploads to Flagsmith**: Sends the collected code references to the Flagsmith API via the Admin API endpoint. The references are associated with the corresponding feature flags in your project.

The scanning process uses regex patterns to find feature flag references in your code. It automatically excludes common build artifacts and dependencies (like `node_modules`, `.git`, `venv`, `.cache`, `dist`, `build`, etc.) to focus on your source code. You can customize the exclusion patterns using the `exclude_patterns` input parameter.

### Example: What Code References Look Like

When the scanner finds a feature flag reference, it collects:
- **File**: `src/components/Header.tsx`
- **Line**: `42`
- **Context**: The code snippet around the reference (typically a few lines before and after)

In the Flagsmith dashboard, you'll see these references listed under each feature flag, allowing you to:
- Click through to the exact file and line in your repository
- See how the flag is being used in context
- Identify all locations where a flag is referenced across your codebase

## Troubleshooting

### Workflow Fails with "Failed to obtain features from Flagsmith"

This error indicates an authentication or API access issue.

**Solutions:**
- Verify your `FLAGSMITH_ADMIN_API_KEY` secret is correctly set in your repository.
- Ensure your API key has the necessary permissions to read project features.
- Check that the `flagsmith_admin_api_url` is correct for your Flagsmith instance.
- Verify your `FLAGSMITH_PROJECT_ID` variable matches a valid project in your Flagsmith organisation.

### Workflow Fails with "Failed to read feature references from code"

This error suggests an issue with the code scanning process.

**Solutions:**
- Check that your repository has code checked out (the workflow handles this automatically).
- Review the workflow logs for specific file access errors.
- Ensure your repository structure is accessible to the GitHub Actions runner.

### Workflow Fails with "Failed to upload code references to Flagsmith"

This error indicates a problem sending data to the Flagsmith API.

**Solutions:**
- Verify your API key has write permissions for code references.
- Check that your Flagsmith instance is accessible from GitHub Actions runners.
- Review the API response in the workflow logs for specific error messages.
- Ensure your project ID is correct and the project exists.

### No Code References Appearing in Flagsmith

If the workflow completes successfully but you don't see references in Flagsmith:

**Solutions:**
- Wait a few moments for the data to process and appear in the UI.
- Refresh the feature flag page in Flagsmith.
- Check that your feature flag names match exactly (case-sensitive) with references in your code.
- Verify the workflow actually found references by checking the workflow logs for a summary of found references.

### Scanning Too Many or Too Few Files

If the scan includes files you want to exclude, or excludes files you want to include:

**Solutions:**
- Use the `exclude_patterns` input to add additional exclusion patterns.
- Review the default exclusion patterns listed in the [What Gets Scanned](#what-gets-scanned) section.
- Ensure your patterns use comma-separated values without spaces.
- For monorepos, you may need to adjust exclusion patterns to focus on specific directories.

### Workflow Completes But Takes Too Long

For large codebases, scans may take several minutes:

**Solutions:**
- Use more specific `exclude_patterns` to reduce the number of files scanned.
- Consider running scans only on specific branches (e.g., `main` and `develop`) rather than all branches.
- Schedule scans during off-peak hours if running on a schedule.
- For very large repositories, consider scanning only specific directories by excluding others.

## Verifying Your Setup

After setting up the integration, verify it's working correctly:

1. **Check workflow execution**: Go to your repository's **Actions** tab and verify the workflow runs successfully. Look for logs showing:
   - Number of features fetched from Flagsmith
   - Number of files scanned
   - Number of references found
   - Successful upload confirmation

2. **Verify in Flagsmith**: Open a feature flag in Flagsmith that you know is used in your codebase. Navigate to the **Code References** tab and confirm you see:
   - File paths where the flag is referenced
   - Line numbers for each reference
   - Code context snippets

3. **Test with a new flag**: Create a test feature flag, add a reference to it in your code, and trigger a manual workflow run. Verify the reference appears in Flagsmith within a few minutes.

## Next Steps

- View code references in Flagsmith by opening any feature flag and checking the **Code References** tab.
- Use code references to identify unused or stale feature flags that can be safely removed.
- Set up notifications or alerts based on code reference changes to track feature flag usage over time.
- Configure multiple trigger types (e.g., daily schedule + pull requests) for comprehensive coverage.

## Related Documentation

- [Flagsmith Admin API](/integrating-with-flagsmith/flagsmith-api-overview/admin-api): Learn more about the Admin API used by this integration.
- [GitHub Actions Documentation](https://docs.github.com/en/actions): Official GitHub Actions documentation for workflow configuration.
