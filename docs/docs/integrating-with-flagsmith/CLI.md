---
description: Flagsmith Command Line Interface (CLI)
sidebar_label: CLI
sidebar_position: 40
---

# Flagsmith CLI

The [Flagsmith CLI](https://github.com/Flagsmith/flagsmith-cli) lets you manage flags, segments, features, projects and
environments from your terminal, and evaluate flags the way an SDK would. This enables CI/CD, scripting, and development
workflows use cases.

:::info

Looking for the previous npm-based CLI (`@flagsmith/cli`)? Its documentation has moved to
[Legacy CLI](/integrating-with-flagsmith/legacy-cli), along with a
[migration guide](/integrating-with-flagsmith/legacy-cli#migrating-to-the-new-cli).

:::

## Installation

Install from Homebrew:

```bash
brew install Flagsmith/tap/flagsmith
```

Or with the install script:

```bash
curl -fsSL https://get.flagsmith.com | sh
```

This installs the binary to `$HOME/.local/bin` and adds it to your `PATH`.

On Windows:

```powershell
irm https://raw.githubusercontent.com/Flagsmith/flagsmith-cli/main/install.ps1 | iex
```

Via NPM:

```bash
npm install -g @flagsmith/cli
```

You can also install with Go, run it via Docker, or download a pre-built archive from
[GitHub Releases](https://github.com/Flagsmith/flagsmith-cli/releases). See the
[README](https://github.com/Flagsmith/flagsmith-cli#install) for all installation options.

## Quickstart

```bash
flagsmith init          # log in, pick a project + environment, write flagsmith.json
flagsmith flag list     # list the flags in the current environment
```

`flagsmith init` creates a `flagsmith.json` file in your current working directory with the project and environment you
selected. The file does not bear any sensitive information and is safe to check in to your repository so your teammates'
CLIs pick up your defaults.

## Usage

The CLI covers flags, segments, features, organisations, projects, environments, SDK-style flag evaluation, and raw API
access. A few examples:

```bash
flagsmith flag enable my_feature                 # toggle a flag in the current environment
flagsmith evaluate --identity some_user          # the flags an SDK would resolve for an identity
flagsmith eval --js > flags.json                 # the state a frontend SDK hydrates from
flagsmith environment document                   # output the local-evaluation environment document
flagsmith api /projects/                         # call any Flagsmith endpoint with the CLI's credentials
```

Common conventions:

- `--json` for machine-readable output; `--jq <expr>` to filter it.
- Static credentials: `FLAGSMITH_API_KEY` (Management API) or `FLAGSMITH_ENVIRONMENT_KEY` (SDK).
- Self-hosted: `--api-url` or `FLAGSMITH_API_URL`.

For the full command reference, see the [README](https://github.com/Flagsmith/flagsmith-cli#commands).

## Using the CLI in CI/CD

### GitHub Actions

Configure an
[OIDC trust relationship](/integrating-with-flagsmith/flagsmith-api-overview/management-api/authentication#oidc-trust-relationships)
for your repository, then use the [`Flagsmith/setup-cli`](https://github.com/Flagsmith/setup-cli) action:

<!-- prettier-ignore -->
```yaml
jobs:
  flagsmith:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v7
      - uses: Flagsmith/setup-cli@v1
      - run: flagsmith flag list
```

The checkout step lets the CLI pick up the project and environment from the `flagsmith.json` file. Without one, select
them explicitly with `--project` and `--environment`.

### Other providers

If your CI provider supports OIDC, you can set up
[a generic trust relationship](/integrating-with-flagsmith/flagsmith-api-overview/management-api/authentication#other-oidc-providers)
for it.

Here are some of the CI providers that support OIDC:

- GitLab CI/CD
- Bitbucket Pipelines
- CircleCI
- Buildkite
- Azure DevOps Pipelines
- Semaphore
- Spacelift
- HCP Terraform / Terraform Enterprise
- Google Cloud Platform (Cloud Build, Cloud Run, Compute Engine)

### Static credentials

On CI systems that don't support OIDC, pass a static credential instead. Management commands expect a
`FLAGSMITH_API_KEY` variable (a
[Master API Key](/integrating-with-flagsmith/flagsmith-api-overview/management-api/authentication#generating-an-api-token)).

If you only need `flagsmith eval`, providing an environment key via `FLAGSMITH_ENVIRONMENT_KEY` variable containing a
[client-side](/integrating-with-flagsmith/flagsmith-api-overview/flags-api/authentication) or
[server-side](/integrating-with-flagsmith/sdks#server-side-sdks) environment key will suffice.

:::info

For self-hosted Flagsmith, the CLI expects static credentials scoped to your API host. For example, for
`https://flagsmith.corp-internal.io:8000`, the CLI will expect `FLAGSMITH_API_KEY_flagsmith_corp__internal_io_8000`.

:::

### Gating pipeline steps on a flag

`flagsmith eval <feature> --test` prints the flag's resolved state and exits non-zero when the flag is disabled, so a
pipeline can gate later steps on it.

In GitHub Actions:

```yaml
- run: flagsmith eval canary-deploys --test
- run: ./deploy.sh
```

Or in a shell script:

```bash
flagsmith eval canary-deploys --test && ./deploy.sh
```
