---
description: Flagsmith Command Line Interface (CLI)
sidebar_label: CLI
sidebar_position: 6
---

# Flagsmith CLI

Flagsmith has a [CLI tool](https://github.com/Flagsmith/flagsmith-cli) that you can use to help in your development
workflows.

## Installation

Install globally:

```bash
npm install -g flagsmith-cli
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
  Retrieve flagsmith features from the Flagsmith API and output them to a file.

EXAMPLES
  $ FLAGSMITH_ENVIRONMENT=x flagsmith get

  $ flagsmith get <ENVIRONMENT_ID>

  $ flagsmith get --o ./my-file.json

  $ flagsmith get --a https://flagsmith.example.com/api/v1/

  $ flagsmith get --i flagsmith_identity
```
