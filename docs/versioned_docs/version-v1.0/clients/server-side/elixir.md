---
title: Flagsmith Elixir SDK
sidebar_label: Elixir
description: Manage your Feature Flags and Remote Config in your Elixir applications.
slug: /clients/elixir
---

This library can be used with server-side Elixir projects. The source code for the client is available on
[Github](https://github.com/flagsmith/flagsmith-elixir-client).

Includes functions and types wrapping the API functionality, schemas and responses.

## Installation

Add to your `mix.exs` `deps`:

### github only while developing

```elixir
def deps do
  [
    {:flagsmith_elixir_sdk, "~> 0.1"}
  ]
end
```

## Configuration

You can configure the SDK per environment using a static default config, for instance in your `config/config.exs`
adding:

```elixir
config :flagsmith_elixir_sdk, :sdk,
       environment_key: "YOUR-ENV-KEY"
```

You can also configure the base url path to use in case you're not using the public API:

```elixir
config :flagsmith_elixir_sdk, :sdk,
       environment_key: "YOUR-ENV-KEY",
       base_url: "YOUR-BASE-URL"
```

For runtime configuration you can create a client struct manually and pass it as the first argument to whatever SDK
function you want to call:

```elixir
{:ok, sdk_client} = Flagsmith.SDK.new("YOUR-ENV-KEY")

Flagsmith.SDK.API.flags_list(sdk_client)

### sample response ###
{:ok, [
   %Flagsmith.API.FeatureStateSerializerFull{
     enabled: false,
     environment: 11278,
     feature: %Flagsmith.API.Feature{
       created_date: ~U[2021-10-24 13:40:02Z],
       default_enabled: false,
       description: "Header Size",
       id: 13534,
       initial_value: "24px",
       name: "header_size",
       type: "MULTIVARIATE"
     },
     feature_segment: nil,
     feature_state_value: "24px",
     id: 72267,
     identity: nil
   },
   %Flagsmith.API.FeatureStateSerializerFull{
     enabled: false,
     environment: 11278,
     feature: %Flagsmith.API.Feature{
       created_date: ~U[2021-10-24 13:41:35Z],
       default_enabled: false,
       description: nil,
       id: 13535,
       initial_value: "18px",
       name: "body_size",
       type: "STANDARD"
     },
     feature_segment: nil,
     feature_state_value: "18px",
     id: 72269,
     identity: nil
   }
 ]}
```

`Flagsmith.SDK.new/2` accepts the base url as the second argument.

## HTTP Client

Underneath the SDK uses [Tesla](https://github.com/teamon/tesla), so you can customise which adapter you want to use.
Refer to `Tesla`'s documentation for additional context.

The default HTTP adapter is Erlang's `httpc`, to use instead, for instance, `hackney`, and the same for any other of the
supported clients, add to your deps the correct dependency:

```elixir
defp deps do
  [
    # ...
    {:hackney, "~> 1.17"}
  ]
end
```

and to your `config/config.exs` the adapter module

```elixir
config :tesla, adapter: Tesla.Adapter.Hackney
```
