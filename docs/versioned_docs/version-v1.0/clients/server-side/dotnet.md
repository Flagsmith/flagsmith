---
title: Flagsmith .Net SDK
sidebar_label: .Net
description: Manage your Feature Flags and Remote Config in your .Net applications.
slug: /clients/dotnet
---

This SDK can be used for .NET Core, .NET Framework, Mono, Xamarin and Universal Windows Platform applications.

The source code for the client is available on [Github](https://github.com/flagsmith/flagsmith-dotnet-client).

## Getting Started

The client library is available from NuGet and can be added to your project by many tools. You can find the package here
[https://www.nuget.org/packages/Flagsmith/](https://www.nuget.org/packages/Flagsmith/)

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your environment key in the Environment settings
page.

![API Key](/img/api-key.png)

## Usage

### Retrieving feature flags for your project

Sign Up and create account at [https://flagsmith.com/](https://www.flagsmith.com/)

In your application initialise the Flagsmith client once with your environment API key and API URL.

```dotnet
FlagsmithConfiguration configuration = new FlagsmithConfiguration()
{
    ApiUrl = "https://api.flagsmith.com/api/v1/",
    EnvironmentKey = "env-key-goes-here"
};

FlagsmithClient client = new FlagsmithClient(configuration);

```

You can then use the `instance` static variable on `FlagsmithClient` anywhere within your app.

To check if a feature flag exists and is enabled:

```dotnet
featureEnabled = (bool)FlagsmithClient.instance.HasFeatureFlag("my_test_feature").GetAwaiter().GetResult();
if (featureEnabled) {
    // run the code to execute enabled feature
} else {
    // run the code if feature switched off
}
```

To get a remote config feature value:

```dotnet
string myRemoteConfig = FlagsmithClient.instance.GetFeatureValue("my_test_feature").GetAwaiter().GetResult();
if (myRemoteConfig != null) {
    // run the code to use remote config value
} else {
    // run the code without remote config
}
```

### Identifying Users

Identifying users allows you to target specific users from the [Flagsmith dashboard](https://www.flagsmith.com/).

To check if a feature exists and is enabled for a specific user:

```dotnet
featureEnabled = (bool)FlagsmithClient.instance.HasFeatureFlag("my_test_feature", "my_user_id").GetAwaiter().GetResult();
if (featureEnabled) {
    // run the code to execute enabled feature for given user
} else {
    // run the code when feature switched off
}
```

To get a remote config value for specific user:

```dotnet

string myRemoteConfig = FlagsmithClient.instance.GetFeatureValue("my_test_feature", "my_user_id").GetAwaiter().GetResult();
if (myRemoteConfig != null) {
    // run the code to use remote config value
} else {
    // run the code without remote config
}
```

To get user traits:

```dotnet
List<Trait> userTraits = FlagsmithClient.instance.GetTraits("my_user_id").GetAwaiter().GetResult();
if (userTraits != null && userTraits) {
    // run the code to use user traits
} else {
    // run the code without user traits
}
```

To get a specific user trait:

```dotnet

string userTrait = FlagsmithClient.instance.GetTrait("my_user_id", "my_user_trait").GetAwaiter().GetResult();
bool userTrait = FlagsmithClient.instance.GetTrait("my_user_id", "my_user_bool_trait").GetAwaiter().GetResult();
int userTrait = FlagsmithClient.instance.GetTrait("my_user_id", "my_user_number_trait").GetAwaiter().GetResult();
```

To get filtered user traits:

```dotnet
List<Trait> userTraits = await FlagsmithClient.instance.GetTrait("my_user_id", new List<string> { "specific_key", /* rest of elements */ });
if (userTraits != null) {
    // run the code to use user traits
} else {
    // run the code without user traits
}
```

To set or update a user trait:

```dotnet
Trait userTrait = await FlagsmithClient.instance.SetTrait("my_user_id", "my_user_trait", "blue");
Trait userTrait = await FlagsmithClient.instance.SetTrait("my_user_id", "my_user_number_trait", 4);
Trait userTrait = await FlagsmithClient.instance.SetTrait("my_user_id", "my_user_bool_trait", true);
```

To increment a numeric user trait:

```dotnet
Trait userTrait = await FlagsmithClient.instance.IncrementTrait("my_user_id", "my_user_number_trait", 1);
```

To retrieve a user identity (both features and traits):

```dotnet
Identity userIdentity = await FlagsmithClient.instance.GetUserIdentity("my_user_id");
if (userIdentity != null) {
  // Run the code to use user identity i.e. userIdentity.flags or userIdentity.traits
}
```
