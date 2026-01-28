---
title: Flag Naming Conventions
sidebar_label: Flag Naming Conventions
sidebar_position: 9
---

Consistent naming conventions make your feature flags easier to understand, search, and manage. This guide covers best practices for naming flags and how to enforce conventions using Flagsmith's built-in validation.

## Why naming conventions matter

Feature flag names serve as identifiers throughout your codebase and within Flagsmith. A clear, consistent naming approach helps your team:

- **Find flags quickly** when searching in the dashboard or code
- **Understand flag purpose** at a glance without reading documentation
- **Avoid naming conflicts** as your flag count grows
- **Maintain consistency** across teams and projects

:::caution
Features cannot be renamed after creation. Choose names carefully, as you'll need to create a new flag and migrate if you want to change a name later.
:::

## Naming best practices

### Use descriptive, self-explanatory names

Flag names should communicate their purpose clearly. Anyone reading the name should understand what the flag controls without needing additional context.

| Recommended | Not recommended | Why |
| --- | --- | --- |
| `show_beta_dashboard` | `flag1` | Describes what the flag controls |
| `enable_stripe_payments` | `payments` | Specifies the integration being toggled |
| `max_upload_size_mb` | `size` | Indicates the value type and unit |
| `allow_guest_checkout` | `gc` | Avoids cryptic abbreviations |

### Choose a consistent format

Pick a naming format and apply it consistently across your project. Common conventions include:

| Format | Example | Notes |
| --- | --- | --- |
| `snake_case` | `enable_dark_mode` | Most common, easy to read |
| `kebab-case` | `enable-dark-mode` | Common in web development |
| `camelCase` | `enableDarkMode` | Matches JavaScript conventions |
| `SCREAMING_SNAKE_CASE` | `ENABLE_DARK_MODE` | Often used for constants |

### Consider prefixes for organisation

Prefixes can help group related flags and make searching easier:

- `feature_` for new functionality: `feature_new_checkout_flow`
- `experiment_` for A/B tests: `experiment_pricing_page_variant`
- `ops_` for operational flags: `ops_maintenance_mode`
- `kill_` for kill switches: `kill_external_api_calls`

### Keep names concise but meaningful

Aim for names that are long enough to be descriptive but short enough to be practical. A good rule of thumb is 2-5 words.

## Enforcing naming conventions

Flagsmith allows you to enforce naming conventions at the project level using regular expressions. When configured, new flags must match the pattern before they can be created.

### Configuring regex validation

1. Navigate to **Project Settings** → **General**
2. Enable **Feature Name RegEx**
3. Enter your regex pattern
4. Click **Save**

Once configured, any attempt to create a flag that doesn't match the pattern will be rejected with a validation error.

### Example regex patterns

Here are common patterns you can use or adapt:

| Pattern | Description | Valid examples |
| --- | --- | --- |
| `^[a-z][a-z0-9_]*$` | Lowercase snake_case | `enable_feature`, `max_retries` |
| `^[a-z][a-z0-9-]*$` | Lowercase kebab-case | `enable-feature`, `max-retries` |
| `^[a-z][a-zA-Z0-9]*$` | camelCase starting lowercase | `enableFeature`, `maxRetries` |
| `^[A-Z][A-Z0-9_]*$` | SCREAMING_SNAKE_CASE | `ENABLE_FEATURE`, `MAX_RETRIES` |
| `^(feature\|experiment\|ops)_[a-z0-9_]+$` | Required prefix with snake_case | `feature_checkout`, `ops_debug` |

:::tip
Test your regex pattern using the **Test RegEx** button before saving. This lets you verify the pattern works as expected with example flag names.
:::

### Pattern requirements

The regex validation in Flagsmith:

- Automatically anchors patterns with `^` at the start and `$` at the end
- Uses standard JavaScript regex syntax
- Applies only to new flags (existing flags are not affected)

## Tag naming conventions

In addition to flag names, consider establishing conventions for [tags](/managing-flags/tagging). Tags help you categorise and filter flags, so consistent naming makes them more useful.

Common tag conventions:

- Use lowercase with hyphens: `backend`, `mobile-app`, `q1-2024`
- Group by purpose: `team-payments`, `team-auth`, `deprecated`
- Include lifecycle stage: `rollout-complete`, `ready-to-remove`

## Further reading

- [Feature Flag Lifecycles](/best-practices/flag-lifecycle) - understanding when to remove flags
- [Structuring Your Projects](/best-practices/structuring-your-projects) - organising flags across projects
- [Tagging](/managing-flags/tagging) - using tags to categorise flags
