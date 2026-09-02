---
description: Legacy Flagsmith Command Line Interface (CLI)
sidebar_label: Legacy CLI
unlisted: true
---

# Flagsmith Legacy CLI

:::warning

The npm-based CLI (`@flagsmith/cli`) is deprecated and no longer maintained. Use the new
[Flagsmith CLI](/integrating-with-flagsmith/CLI) instead — see [Migrating to the new CLI](#migrating-to-the-new-cli).

:::

## Migrating to the new CLI

The legacy CLI's `flagsmith get` command is reimplemented as `flagsmith eval --js`:

```bash
# Before
FLAGSMITH_ENVIRONMENT=<key> flagsmith get

# After
FLAGSMITH_ENVIRONMENT_KEY=<key> flagsmith eval --js > flags.json
```

The options map as follows:

| Legacy CLI                       | New CLI                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `ENVIRONMENT` argument           | `--environment <key>`, or `flagsmith init` to bind the directory                |
| `FLAGSMITH_ENVIRONMENT` variable | `FLAGSMITH_ENVIRONMENT_KEY`                                                     |
| `-o, --output <file>`            | Redirect stdout: `> flags.json`                                                 |
| `-a, --api <url>`                | `--sdk-api-url <url>` or `FLAGSMITH_SDK_API_URL`, without the `/api/v1/` suffix |
| `-i, --identity <identity>`      | `--identity <identity>`                                                         |

## Installation

Install globally:

```bash
npm install -g @flagsmith/cli
```

## Sample Usage

```bash
USAGE
  $ flagsmith get [ENVIRONMENT] [-o <value>] [-a <value>] [-i <value>]

ARGUMENTS
  ENVIRONMENT  The flagsmith environment key to use,
  defaults to the environment variable FLAGSMITH_ENVIRONMENT

FLAGS
  -a, --api=<value>       The API URL to fetch the feature flags from
  -i, --identity=<value>  The identity for which to fetch feature flags
  -o, --output=<value>    [default: ./flagsmith.json] The file path output

DESCRIPTION
  Retrieve flagsmith feature flags from the Flagsmith API and output them to a file.

EXAMPLES
  $ FLAGSMITH_ENVIRONMENT=x flagsmith get

  $ flagsmith get <ENVIRONMENT_ID>

  $ flagsmith get --o ./my-file.json

  $ flagsmith get --a https://flagsmith.example.com/api/v1/

  $ flagsmith get --i flagsmith_identity
```
