---
title: Flagsmith Ruby SDK
sidebar_label: Ruby
description: Manage your Feature Flags and Remote Config in your Ruby applications.
slug: /clients/ruby
---

The SDK clients for Ruby [https://flagsmith.com/](https://www.flagsmith.com/). Flagsmith allows you to manage feature
flags and remote config across multiple projects, environments and organisations.

The source code for the client is available on [Github](https://github.com/flagsmith/flagsmith-ruby-client).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing
purposes. See running in production for notes on how to deploy the project on a live system.

## Installing

VIA gem:

`gem install flagsmith`

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your environment key in the Environment settings
page.

![API Key](/img/api-key.png)

## Usage

### Retrieving feature flags for your project

```ruby
require "flagsmith"

flagsmith = Flagsmith.new("<<Your API KEY>>")

if flagsmith.get_value("font_size")
  #    Do something awesome with the font size
end

if flagsmith.feature_enabled?("does_not_exist")
  #do something
else
  #do nothing, or something else
end
```

## Available Options

| Property  |                                            Description                                            | Required |                       Default Value |   Environment Key |
| --------- | :-----------------------------------------------------------------------------------------------: | -------: | ----------------------------------: | ----------------: |
| `api_key` |  Defines which project environment you wish to get flags for. _example ACME Project - Staging._   |  **YES** |                                null | FLAGSMITH_API_KEY |
| `url`     | Use this property to define where you're getting feature flags from, e.g. if you're self hosting. |   **NO** | <https://api.flagsmith.com/api/v1/> |     FLAGSMITH_URL |

## Available Functions

| Property                                          |                                                     Description                                                      |
| ------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------: |
| `init`                                            |                                 Initialize the sdk against a particular environment                                  |
| `feature_enabled?(key)`                           |         Get the value of a particular feature e.g. `flagsmith.feature_enabled?("powerUserFeature") // true`          |
| `feature_enabled?(key, user_id, default = false)` | Get the value of a particular feature for a user e.g. `flagsmith.feature_enabled?("powerUserFeature", 1234) // true` |
| `get_value(key)`                                  |                 Get the value of a particular feature e.g. `flagsmith.get_value("font_size") // 10`                  |
| `get_value(key, user_id, default = nil)`          |    Get the value of a particular feature for a specified user e.g. `flagsmith.get_value("font_size", 1234) // 15`    |
| `get_flags()`                                     |       Trigger a manual fetch of the environment features, if a user is identified it will fetch their features       |
| `get_flags(user_id)`                              |                       Trigger a manual fetch of the environment features with a given user id                        |
| `set_trait(user_id, trait, value)`                |                                    Set the value of a trait for the given user id                                    |

## Identifying Users

Identifying users allows you to target specific users from the [Flagsmith dashboard](https://www.flagsmith.com/). You
can include an optional user identifier as part of the `feature_enabled?` and `get_value` methods to retrieve unique
user flags and variables.
