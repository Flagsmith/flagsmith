---
title: Flagsmith Python SDK
sidebar_label: Python
description: Manage your Feature Flags and Remote Config in your Python applications.
slug: /clients/python
---

This library can be used with server-side Python projects. The source code for the client is available on
[Github](https://github.com/flagsmith/flagsmith-python-client).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing
purposes. See running in production for notes on how to deploy the project on a live system.

## Installing

### VIA pip

```bash
pip install flagsmith
```

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your environment key in the Environment settings
page.

![API Key](/img/api-key.png)

## Usage

### Retrieving feature flags for your project

```python
from flagsmith import Flagsmith

flagsmith = Flagsmith(environment_id="<YOUR_ENVIRONMENT_KEY>")

if flagsmith.has_feature("header"):
  if flagsmith.feature_enabled("header"):
    # Show my awesome cool new feature to the world

value = flagsmith.get_value("header", '<My User Id>')

value = flagsmith.get_value("header")

flagsmith.set_trait("accept-cookies", "true", "ben@flagsmith.com")
flagsmith.get_trait("accept-cookies", "ben@flagsmith.com")
```

### Available Options

| Property         | Description                                                                                       | Required |                       Default Value |
| ---------------- | :------------------------------------------------------------------------------------------------ | -------: | ----------------------------------: |
| `environment_id` | Defines which project environment you wish to get flags for. _example ACME Project - Staging._    |  **YES** |                                None |
| `api`            | Use this property to define where you're getting feature flags from, e.g. if you're self hosting. |   **NO** | <https://api.flagsmith.com/api/v1/> |

### Available Functions

| Function                                    |                                                             Description                                                              |
| ------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------: |
| `has_feature(key)`                          |                  Determine if given feature exists for an environment. `bt.has_feature("powerUserFeature") // true`                  |
| `feature_enabled(key)`                      |                  Get the value of a particular _feature flag_ e.g. `bt.feature_enabled("powerUserFeature") // true`                  |
| `feature_enabled(key, userId)`              |               Get the value of a particular _feature flag_ e.g. `bt.feature_enabled("powerUserFeature", 1234) // true`               |
| `get_value(key)`                            |                         Get the value of a particular _remote config_ e.g. `bt.get_value("font_size") // 10`                         |
| `get_value(key, userId)`                    |               Get the value of a particular feature for a specified user e.g. `bt.get_value("font_size", 1234) // 15`                |
| `set_trait(trait_key, trait_value, userId)` |              Set the value of a particular trait for a specified user e.g. `bt.set_trait("font_size", 12, 1234) // 15`               |
| `get_trait(trait_key, userId)`              |                Get the value of a particular trait for a specified user e.g. `bt.get_trait("font_size", 1234) // 12`                 |
| `get_flags()`                               |           Trigger a manual fetch of the environment features, returns a list of flag objects, see below for returned data            |
| `get_flags_for_user(1234)`                  | Trigger a manual fetch of the environment features with a given user id, returns a list of flag objects, see below for returned data |

### Identifying users

Identifying users allows you to target specific users from the [Flagsmith dashboard](https://flagsmith.com/). You can
include an optional user identifier as part of the `has_feature` and `get_value` methods to retrieve unique user flags
and variables.

### Flags data structure

| Field               | Description                            | Type                                                                            |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------------------- |
| id                  | Internal id of feature state           | Integer                                                                         |
| enabled             | Whether feature is enabled or not      | Boolean                                                                         |
| environment         | Internal ID of environment             | Integer                                                                         |
| feature_state_value | Value of the feature                   | Any - determined based on data input on [flagsmith.com](https://flagsmith.com). |
| feature             | Feature object - see below for details | Object                                                                          |

### Feature data structure

| Field        | Description                                                        | Type     |
| ------------ | ------------------------------------------------------------------ | -------- |
| id           | Internal id of feature                                             | Integer  |
| name         | Name of the feature (sometimes referred to as key or ID)           | String   |
| description  | Description of the feature                                         | String   |
| type         | Feature Type. Can be FLAG or CONFIG                                | String   |
| created_date | Date feature was created                                           | Datetime |
| inital_value | The initial / default value set for all feature states on creation | String   |
| project      | Internal ID of the associated project                              | Integer  |
