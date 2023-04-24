---
title: Flagsmith Go SDK
sidebar_label: Go
description: Manage your Feature Flags and Remote Config in your Go applications.
slug: /clients/go
---

The SDK client for Go [https://flagsmith.com/](https://www.flagsmith.com/). Flagsmith allows you to manage feature flags
and remote config across multiple projects, environments and organisations.

The source code for the client is available on [Github](https://github.com/flagsmith/flagsmith-go-client).

## Getting Started

```bash
go get github.com/Flagsmith/flagsmith-go-client
```

```go
import (
  "github.com/Flagsmith/flagsmith-go-client"
)
```

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your environment key in the Environment settings
page.

![API Key](/img/api-key.png)

## Retrieving feature flags for your project

For full documentation visit [https://docs.flagsmith.com](https://docs.flagsmith.com)

Sign Up and create account at [https://flagsmith.com/](https://www.flagsmith.com/)

In your application initialise the Flagsmith client with your API key

```go
fs := flagsmith.DefaultClient("<Your API Key>")
```

To check if a feature flag exists and is enabled:

```go
fs := flagsmith.DefaultClient("<Your API Key>")
enabled, err := fs.FeatureEnabled("cart_abundant_notification_ab_test_enabled")
if err != nil {
    log.Fatal(err)
} else {
    if (enabled) {
        fmt.Printf("Feature enabled")
    }
}
```

To get the configuration value for feature flag value:

```go
feature_value, err := fs.GetValue("cart_abundant_notification_ab_test")
if err != nil {
    log.Fatal(err)
} else {
    fmt.Printf(feature_value)
}
```

More examples can be found in the [Tests](https://github.com/Flagsmith/flagsmith-go-client/blob/main/client_test.go)

## Override default configuration

By default, client is using default configuration. You can override configuration as follows:

```go
fs := flagsmith.NewClient("<Your API Key>", flagsmith.Config{BaseURI: "<Your API URL>"})
```
