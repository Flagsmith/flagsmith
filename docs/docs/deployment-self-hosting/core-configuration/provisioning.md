---
title: 'Provisioning'
description: 'Declaratively configure your Flagsmith instance using YAML files.'
sidebar_position: 15
---

# Provisioning

Provisioning lets you declaratively define the desired state of a Flagsmith instance in YAML files. On startup (or on
demand), the `provision` management command reads these files and creates any entities that do not already exist.

Use provisioning when you want **repeatable, headless setup** in IaC scenarios. For interactive setup, see the
[Initial Setup](/deployment-self-hosting/core-configuration/initial-setup) page. For ongoing flag management via API,
see the [Terraform provider](https://github.com/Flagsmith/terraform-provider-flagsmith).

## Quick start

1. Create a YAML file at `provisioning/bootstrap.yaml`:

```yaml
version: '1.0'

app_domain: '${APP_DOMAIN:localhost:8000}'

users:
 - email: '${ADMIN_EMAIL:admin@example.com}'
   is_superuser: true

organisations:
 - name: '${ORGANISATION_NAME:Default Organisation}'
   members:
    - email: '${ADMIN_EMAIL:admin@example.com}'
      role: ADMIN

projects:
 - name: '${PROJECT_NAME:Default Project}'
   organisation: '${ORGANISATION_NAME:Default Organisation}'
```

2. Run the provisioner:

```bash
python manage.py provision
```

3. Expected output:

```
Created user "admin@example.com".
Please go to the following page and choose a password: http://localhost:8000/password-reset/confirm/…/…
Created organisation "Default Organisation".
Created project "Default Project".
Provisioning complete: 3 created, 0 skipped.
```

## Provisioning files

### YAML format

Each provisioning file is a YAML document with a required `version` field, optional top-level settings, and one or more
entity lists. Files must use the `.yaml` or `.yml` extension.

```yaml
version: '1.0'

app_domain: 'flagsmith.example.com'

users:
 - email: 'admin@example.com'
   is_superuser: true

organisations:
 - name: 'My Organisation'
   # ...
```

### Top-level settings

| Key          | Description                                                                                                      | Default             |
| ------------ | ---------------------------------------------------------------------------------------------------------------- | ------------------- |
| `version`    | Schema version (required). Currently `"1.0"`.                                                                    |                     |
| `app_domain` | The domain where the Flagsmith frontend is served. Used for password reset links, invite emails, and other URLs. | `app.flagsmith.com` |

`app_domain` sets the Django `Site.domain` value. If you have already set the `FLAGSMITH_DOMAIN` environment variable,
that takes precedence.

### File discovery

When you point the provisioner at a directory, it reads every `.yaml` / `.yml` file in that directory (non-recursively)
and processes them **in alphabetical order**. Use numeric prefixes to control ordering:

```
provisioning/
  00-users.yaml
  10-organisations.yaml
  20-projects.yaml
  30-features.yaml
```

### Environment variable interpolation

Use `${VAR}` or `${VAR:default}` anywhere in a YAML value. The provisioner resolves these from the process environment
before parsing the YAML.

```yaml
users:
 - email: '${ADMIN_EMAIL:admin@example.com}' # falls back to admin@example.com
   is_superuser: true

organisations:
 - name: '${ORGANISATION_NAME}' # required — fails if unset
```

### Entity references

Use string values to reference entities defined elsewhere. The provisioner resolves references after all files have been
loaded, so you can split definitions across files freely.

```yaml
# In 10-organisations.yaml
organisations:
 - name: 'Acme Corp'

# In 20-projects.yaml
projects:
 - name: 'Web App'
   organisation: 'Acme Corp' # references the organisation by name
   environments:
    - name: 'Development'
    - name: 'Production'
```

## Entity kinds

The table below summarises every supported entity kind. Required fields are marked with **bold**. All entities support
an optional `description` field.

| Kind             | Idempotency key         | Required fields            | Optional fields                        |
| ---------------- | ----------------------- | -------------------------- | -------------------------------------- |
| `user`           | `email`                 | **email**                  | `is_superuser`                         |
| `organisation`   | `name`                  | **name**                   | `members`, `subscription`              |
| `project`        | `name` + `organisation` | **name**, **organisation** | `environments`, `features`, `segments` |
| `environment`    | `name` + `project`      | **name**                   | (nested under `project`)               |
| `feature`        | `name` + `project`      | **name**                   | `default_enabled`, `initial_value`     |
| `segment`        | `name` + `project`      | **name**                   | `rules`                                |
| `master_api_key` | `name` + `organisation` | **name**, **organisation** | `is_admin`                             |

### Processing order

Entities are processed in dependency order regardless of where they appear in the YAML files:

```
users → organisations (+ members, subscription) → master_api_keys → projects → environments → segments → features
```

### User

Creates a Flagsmith user account. If `is_superuser` is true, the user is created as a Django superuser with no password;
a password-reset link is printed to the console.

```yaml
users:
 - email: 'admin@example.com'
   is_superuser: true

 - email: 'developer@example.com'
```

### Organisation

Creates an organisation and optionally adds members and configures a subscription.

```yaml
organisations:
 - name: 'Acme Corp'
   members:
    - email: 'admin@example.com'
      role: ADMIN
    - email: 'developer@example.com'
      role: USER
   subscription:
    plan: 'enterprise'
    seats: 20
```

### Project

Creates a project within an organisation. Environments, features, and segments can be nested inline or defined as
separate top-level entities referencing the project.

```yaml
projects:
 - name: 'Web App'
   organisation: 'Acme Corp'
   environments:
    - name: 'Development'
    - name: 'Staging'
    - name: 'Production'
   features:
    - name: 'dark_mode'
      default_enabled: false
    - name: 'api_url'
      initial_value: 'https://api.example.com'
   segments:
    - name: 'beta_users'
      rules:
       - type: ALL
         conditions:
          - property: 'is_beta'
            operator: EQUAL
            value: 'true'
```

### Environment

Environments are typically nested under a project, but can also be defined at the top level.

```yaml
environments:
 - name: 'QA'
   project: 'Web App'
```

### Feature

Features with `default_enabled` act as boolean flags. Features with `initial_value` act as remote config.

```yaml
features:
 - name: 'maintenance_mode'
   project: 'Web App'
   default_enabled: false

 - name: 'items_per_page'
   project: 'Web App'
   initial_value: '25'
```

### Segment

Segments define rules with conditions that use operators such as `EQUAL`, `NOT_EQUAL`, `CONTAINS`, `NOT_CONTAINS`,
`GREATER_THAN`, `LESS_THAN`, `GREATER_THAN_INCLUSIVE`, `LESS_THAN_INCLUSIVE`, `REGEX`, `PERCENTAGE_SPLIT`, `IN`, and
`IS_SET` / `IS_NOT_SET`.

```yaml
segments:
 - name: 'enterprise_customers'
   project: 'Web App'
   rules:
    - type: ALL
      conditions:
       - property: 'plan'
         operator: EQUAL
         value: 'enterprise'
```

### Master API key

Creates a master API key for an organisation. The key value is **only available at creation time** — only the prefix and
hash are stored. The provisioner prints the full key to the console on creation.

```yaml
master_api_keys:
 - name: 'CI/CD Pipeline Key'
   organisation: 'Acme Corp'
   is_admin: true
```

Output:

```
Created master API key "CI/CD Pipeline Key": flg_masXXXXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

:::caution

Store the master API key securely — it cannot be retrieved after provisioning completes.

:::

## Management command reference

```bash
python manage.py provision [OPTIONS]
```

| Option         | Description                                                       | Default         |
| -------------- | ----------------------------------------------------------------- | --------------- |
| (no arguments) | Provision from the default directory                              | `provisioning/` |
| `--directory`  | Read all YAML files from the given directory (alphabetical order) |                 |
| `--file`       | Provision from a single YAML file                                 |                 |
| `--dry-run`    | Validate files and print what would be created, without writing   |                 |

Examples:

```bash
# Use the default provisioning directory
python manage.py provision

# Use a custom directory
python manage.py provision --directory /etc/flagsmith/provisioning/

# Provision from a single file
python manage.py provision --file provisioning/bootstrap.yaml

# Validate without making changes
python manage.py provision --dry-run
```

### Output format

The command prints one line per entity action and a summary at the end:

```
Created user "admin@example.com".
Skipped organisation "Acme Corp" (already exists).
Created project "Web App".
Created environment "Development" in project "Web App".
Created environment "Production" in project "Web App".
Created feature "dark_mode" in project "Web App".
Provisioning complete: 4 created, 1 skipped.
```

## Idempotency

The provisioner uses **create-only / skip-if-exists** semantics. Each entity kind has an idempotency key (see the
[Entity kinds](#entity-kinds) table). If an entity with the same key already exists, the provisioner skips it and logs a
message. It does **not** update or delete existing entities.

This means you can safely re-run the provisioner — for example, on every container startup — without duplicating data or
overwriting manual changes.

| Scenario                           | Behaviour                                  |
| ---------------------------------- | ------------------------------------------ |
| Entity does not exist              | Created                                    |
| Entity already exists (same key)   | Skipped                                    |
| Entity was modified after creation | Not overwritten — manual changes preserved |
| Entity was deleted                 | Re-created on next run                     |

## Use case guides

### Self-hosted bootstrap

The provisioner replaces the existing `bootstrap` management command for new deployments. The same environment variables
work via interpolation:

| Existing variable                | Provisioning equivalent                     |
| -------------------------------- | ------------------------------------------- |
| `ADMIN_EMAIL`                    | `${ADMIN_EMAIL:admin@example.com}`          |
| `ORGANISATION_NAME`              | `${ORGANISATION_NAME:Default Organisation}` |
| `PROJECT_NAME`                   | `${PROJECT_NAME:Default Project}`           |
| `ALLOW_ADMIN_INITIATION_VIA_CLI` | No longer needed — use `provision` command  |

The Docker entrypoint (`run-docker.sh`) calls `provision` in the `migrate-and-serve` flow. The web-based initialisation
form at `/api/v1/users/config/init/` remains available for interactive setup (controlled by
`ALLOW_ADMIN_INITIATION_VIA_URL`).

**Default bootstrap file**

A `provisioning/bootstrap.yaml` file ships with Flagsmith and replicates the current `bootstrap` behaviour:

```yaml
version: '1.0'

app_domain: '${APP_DOMAIN:localhost:8000}'

users:
 - email: '${ADMIN_EMAIL:admin@example.com}'
   is_superuser: true

organisations:
 - name: '${ORGANISATION_NAME:Default Organisation}'
   members:
    - email: '${ADMIN_EMAIL:admin@example.com}'
      role: ADMIN

projects:
 - name: '${PROJECT_NAME:Default Project}'
   organisation: '${ORGANISATION_NAME:Default Organisation}'
```

### Kubernetes / Helm

Mount provisioning YAML files as a ConfigMap or Secret and point the provisioner at the mount path.

**ConfigMap example:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
 name: flagsmith-provisioning
data:
 00-bootstrap.yaml: |
  version: "1.0"
  users:
    - email: "admin@acme.com"
      is_superuser: true
  organisations:
    - name: "Acme Corp"
      members:
        - email: "admin@acme.com"
          role: ADMIN
  projects:
    - name: "Production"
      organisation: "Acme Corp"
      environments:
        - name: "Production"
        - name: "Staging"
```

**Helm values snippet:**

```yaml
api:
 extraVolumes:
  - name: provisioning
    configMap:
     name: flagsmith-provisioning
 extraVolumeMounts:
  - name: provisioning
    mountPath: /etc/flagsmith/provisioning/
 extraEnv:
  - name: PROVISIONING_DIRECTORY
    value: /etc/flagsmith/provisioning/
```

### Flagsmith on Flagsmith

Automate the creation of the project and flags needed to run
[Flagsmith on Flagsmith](/deployment-self-hosting/core-configuration/running-flagsmith-on-flagsmith).

```yaml
version: '1.0'

projects:
 - name: 'Flagsmith on Flagsmith'
   organisation: '${ORGANISATION_NAME:Default Organisation}'
   environments:
    - name: 'Production'
   features:
    - name: 'oauth_google'
      initial_value: '{"clientId": "${GOOGLE_OAUTH_CLIENT_ID}"}'
    - name: 'dark_mode'
      default_enabled: true

master_api_keys:
 - name: 'Flagsmith on Flagsmith Key'
   organisation: '${ORGANISATION_NAME:Default Organisation}'
   is_admin: true
```

After provisioning, copy the master API key from the output and set `FLAGSMITH_ON_FLAGSMITH_API_KEY` on the frontend.

### CI/CD integration

Provision master API keys for headless pipelines. The provisioner prints the key value at creation time; capture it in
your script:

```bash
# Provision and capture output
OUTPUT=$(python manage.py provision --file provisioning/ci.yaml)

# Extract the master API key
API_KEY=$(echo "$OUTPUT" | grep "Created master API key" | grep -oP 'flg_mas\S+')

# Use the key in subsequent API calls
curl -H "Authorization: Api-Key $API_KEY" \
     http://localhost:8000/api/v1/organisations/
```

## Environment variables reference

| Variable                         | Description                                                              | Default                |
| -------------------------------- | ------------------------------------------------------------------------ | ---------------------- |
| `PROVISIONING_DIRECTORY`         | Directory to read provisioning YAML files from                           | `provisioning/`        |
| `ADMIN_EMAIL`                    | Email for the initial superuser (used via interpolation)                 | `admin@example.com`    |
| `ORGANISATION_NAME`              | Name for the initial organisation (used via interpolation)               | `Default Organisation` |
| `PROJECT_NAME`                   | Name for the initial project (used via interpolation)                    | `Default Project`      |
| `ALLOW_ADMIN_INITIATION_VIA_URL` | Enable the web-based initialisation form at `/api/v1/users/config/init/` | `true`                 |
