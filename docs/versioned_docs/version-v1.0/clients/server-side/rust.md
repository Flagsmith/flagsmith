---
title: Flagsmith Rust SDK
sidebar_label: Rust
description: Manage your Feature Flags and Remote Config in your Rust applications.
slug: /clients/rust
---

The SDK client for Rust [https://flagsmith.com/](https://www.flagsmith.com/). Flagsmith allows you to manage feature
flags and remote config across multiple projects, environments and organisations.

The source code for the client is available on [Github](https://github.com/flagsmith/flagsmith-rust-client).

The client SDK is published to [Crates](https://crates.io/crates/flagsmith)

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your environment key in the Environment settings
page.

![API Key](/img/api-key.png)

## Usage

### Retrieving feature flags for your project

In your application initialise the Flagsmith client with your API key

```rust
let flagsmith = flagsmith::Client::new("<Your API Key>");
```

To check if a feature flag exists and is enabled:

```rust
let flagsmith = flagsmith::Client::new("<Your API Key>");
if flagsmith.feature_enabled("cart_abundant_notification_ab_test_enabled")? {
    println!("Feature enabled");
}
```

To get the configuration value for feature flag value:

```rust
use flagsmith::{Client,Value};

let flagsmith = Client::new("<Your API Key>");

if let Some(Value::String(s)) = bt.get_value("cart_abundant_notification_ab_test")? {
    println!("{}", s);
}
```

More examples can be found in the
[Tests](https://github.com/Flagsmith/flagsmith-rust-client/blob/main/tests/integration_test.rs)

## Override default configuration

By default, client is using default configuration. You can override configuration as follows:

```rust
let flagsmith = flagsmith::Client {
    api_key: String::from("secret key"),
    base_uri: String::from("https://features.on.my.own.server/api/v1/"),
};
```
