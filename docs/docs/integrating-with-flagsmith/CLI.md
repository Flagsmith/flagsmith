---
description: Flagsmith Command Line Interface (CLI)
sidebar_label: CLI
sidebar_position: 40
---

# Flagsmith CLI

The [Flagsmith CLI](https://github.com/Flagsmith/flagsmith-cli) lets you manage flags, segments, features, projects and
environments from your terminal, and evaluate flags the way an SDK would. This enables CI/CD, scripting, and
development workflows use cases.

:::info

The Flagsmith CLI V2 is currently in open beta. We're excited for you to try it and provide any feedback via [GitHub Issues](https://github.com/Flagsmith/flagsmith-cli/issues).

:::

:::info

Looking for the previous npm-based CLI (`@flagsmith/cli`)? Its documentation has moved to
[Legacy CLI](/integrating-with-flagsmith/legacy-cli).

:::

## Installation

Install with the install script:

```bash
curl -fsSL https://raw.githubusercontent.com/Flagsmith/flagsmith-cli/main/install.sh | sh
```

This installs the binary to `$HOME/.local/bin` and adds it to your `PATH`.

On Windows:

```powershell
irm https://raw.githubusercontent.com/Flagsmith/flagsmith-cli/main/install.ps1 | iex
```

You can also install with Go, run it via Docker, or download a pre-built archive from [GitHub Releases](https://github.com/Flagsmith/flagsmith-cli/releases).
See the [README](https://github.com/Flagsmith/flagsmith-cli#install) for all installation options.

## Quickstart

```bash
flagsmith init          # log in, pick a project + environment, write flagsmith.json
flagsmith flag list     # list the flags in the current environment
```

## Usage

The CLI covers flags, segments, features, organisations, projects, environments, SDK-style flag evaluation, and raw API
access. A few examples:

```bash
flagsmith flag enable my_feature                 # toggle a flag in the current environment
flagsmith evaluate --identity some_user          # the flags an SDK would resolve for an identity
flagsmith environment document                   # output the local-evaluation environment document
flagsmith api /projects/                         # call any Flagsmith endpoint with the CLI's credentials
```

Common conventions:

- `--json` for machine-readable output; `--jq <expr>` to filter it.
- Static credentials: `FLAGSMITH_API_KEY` (Admin API) or `FLAGSMITH_ENVIRONMENT_KEY` (SDK).
- Self-hosted: `--api-url` or `FLAGSMITH_API_URL`.

For the full command reference, see the [README](https://github.com/Flagsmith/flagsmith-cli#commands).
