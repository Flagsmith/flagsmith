---
title: Flagsmith Flutter SDK
sidebar_label: Flutter
description: Manage your Feature Flags and Remote Config in your Flutter applications.
slug: /clients/flutter
---

This SDK can be used for Flutter applications. The source code for the client is available on
[GitHub](https://github.com/flagsmith/flagsmith-flutter-client).

The Flagsmith Flutter SDK supports iOS, Android and Web targets.

## Getting Started

The client library is available from the [https://pub.dev/packages/flagsmith](https://pub.dev/packages/flagsmith):

```dart
dependencies:
  flagsmith:
```

## Basic Usage

The SDK is initialised against a single Environment. You can find your Environment key in the Environment settings page.

### Retrieving feature flags for your project

In your application, initialise the Flagsmith client with your API key:

```dart
import 'package:flagsmith/flagsmith.dart';

final flagsmithClient = FlagsmithClient(
        apiKey: 'YOUR_ENV_API_KEY'
        config: config,
        seeds: <Flag>[
            Flag.seed('feature', enabled: true),
        ],
    );
await flagsmithClient.initialize();
await flagsmithClient.getFeatureFlags(reload: true) // fetch updates from api
```

If you prefer async initialization then you can use:

```dart
import 'package:flagsmith/flagsmith.dart';

final flagsmithClient = await FlagsmithClient.init(
        apiKey: 'YOUR_ENV_API_KEY',
        config: config,
        seeds: <Flag>[
            Flag.seed('feature', enabled: true),
        ],
    );
await flagsmithClient.getFeatureFlags(reload: true) // fetch updates from api
```

To check if a feature flag exists:

```dart
bool featureExists = await flagsmithClient.hasFeatureFlag("my_test_feature");
```

Check if a feature flag exist and is enabled:

```dart
bool featureEnabled = await flagsmithClient.isFeatureFlagEnabled("my_test_feature");
if (featureEnabled) {
    // run the code to execute enabled feature
} else {
    // run the code if feature switched off
}
```

To get the configuration value for a feature flag:

```dart
final myRemoteConfig = await flagsmithClient.getFeatureFlagValue("my_test_feature");
if (myRemoteConfig != null) {
    // run the code to use remote config value
} else {
    // run the code without remote config
}
```

To listen for fetch request state:

```dart
flagsmithClient.loading.listen((state){
    // FlagsmithLoading.loading
    // FlagsmithLoading.loaded
});
```

To listen for feature flag changes:

```dart
flagsmithClient.stream("my_test_feature").listen((value){
    // call to action
});
```

```dart
StreamBuilder(
    stream: flagsmithClient.stream("my_test_feature"),
    builder: (context, AsyncSnapshot<String> snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
            return CircularProgressIndicator();
        }
        return TextButton(
            onPressed: snapshot.data.enabled ? (){} : null,
            child: Text('Call to Action'),);
    },
),
```

## Cached flags

You can use caches instead of async/await:

```dart
final config = FlagsmithConfig(
    baseURI: 'http://yoururl.com/',
    connectTimeout: 200,
    receiveTimeout: 500,
    sendTimeout: 500,
    storeType = StoreType.inMemory,
    caches: true, // mandatory if you want to use caches
);
await flagsmithClient.initialize();

final flagsmithClient = await FlagsmithClient.init(
        apiKey: 'YOUR_ENV_API_KEY',
        config: config,
        seeds: <Flag>[
            Flag.seed('feature', enabled: true),
        ],
    );

await flagsmithClient.getFeatureFlags(reload: true); // fetch updates from api
bool isFeatureEnabled = flagsmithClient.hasCachedFeatureFlag('feature');
```

### Identifying users

To check if a feature exists for an Identity:

```dart
final user = Identity(identifier: 'flagsmith_sample_user');
bool featureEnabled = await flagsmithClient.hasFeatureFlag('my_test_feature', user: user);
if (featureEnabled) {
    // run the code to execute enabled feature for given user
} else {
    // run the code when feature switched off
}
```

To get the feature flag configuration value for an Identity:

```dart
final myRemoteConfig = await flagsmithClient.getFeatureFlagValue('my_test_feature', user: user);
if (myRemoteConfig != null) {
    // run the code to use remote config value
} else {
    // run the code without remote config
}
```

To get the user traits for an Identity:

```dart
final userTraits = await flagsmithClient.getTraits(user)
if (userTraits != null && userTraits) {
    // run the code to use user traits
} else {
    // run the code without user traits
}
```

To get the trait value for an Identity and specific Trait key:

```dart
final userTrait = await flagsmithClient.getTrait(user, 'cookies_key');
if (userTrait != null) {
    // run the code to use user trait
} else {
    // run the code without user trait
}
```

Or get user traits for an Identity and specific Trait keys:

```dart
final userTraits = await flagsmithClient.getTraits(user, keys: ['cookies_key', 'other_trait']);
if (userTraits != null) {
    // run the code to use user traits
} else {
    // run the code without user traits
}
```

To update a user trait for an Identity:

```dart
final userTrait = await flagsmithClient.getTrait(user, 'cookies_key');
if (userTrait != null) {
    // update value for user trait
    var updatedTrait = userTrait.copyWith(value: 'new value');
    Trait updated = await flagsmithClient.updateTrait(user, updatedTrait);
} else {
    // run the code without user trait
}
```

## Reset storage

To reset storage and re-seed default values:

```dart
await flagsmithClient.reset();
```

## Override default configuration

By default, the client uses the default configuration. You can override this configuration as follows:

```dart
final flagsmithClient = FlagsmithClient(
      config: FlagsmithConfig(
          baseURI: 'http://yoururl.com/'
      ), apiKey: 'YOUR_ENV_API_KEY');
```

Override the default configuration with your own:

```dart
final flagsmithClient = FlagsmithClient(
      config: FlagsmithConfig(
          baseURI: 'http://yoururl.com/',
          connectTimeout: 200,
          receiveTimeout: 500,
          sendTimeout: 500,
          storeType = StoreType.inMemory,
          caches: true,
      ), apiKey: 'YOUR_ENV_API_KEY');
```

## Real-time Flag Updates

:::tip

Real-time Flags are part of our SaaS Scale-Up and Enterprise plans.

Real-time Flags are currently in beta. Please contact us to join the beta!

:::

Real-time flag updates are disabled by default. You can enable them simply by changing the configuration as follows:

```dart
final flagsmithClient = FlagsmithClient(
      config: FlagsmithConfig(
          enableRealtimeUpdates: true,
      ), apiKey: 'YOUR_ENV_API_KEY');
```

This will use the default Flagsmith realtime updates URI: `'https://realtime.flagsmith.com/sse/environments/'`, with a
reconnect interval of 29000 milliseconds.

You can change this configuration with your own SSE connection:

```dart
final flagsmithClient = FlagsmithClient(
      config: FlagsmithConfig(
          enableRealtimeUpdates: true,
          realtimeUpdatesBaseURI: 'https://your_sse_endpoint.com/sse/',
          reconnctToSSEInterval: 15000,
      ), apiKey: 'YOUR_ENV_API_KEY');
```

## Known issues

- If using the package Dio, you may encounter an error saying `Bad state: Future already completed`. There is a bug in
  the Dio package, introduced in 4.0.5 (and as of writing this on 12/09/2022, is unresolved). To resolve, you'll need to
  pin your Dio version in pubspec.yaml to 4.0.4 or earlier. You can track the state of this issue
  [here within our repo](https://github.com/Flagsmith/flagsmith-flutter-client/issues/45) and also at the
  [dio repo](https://github.com/flutterchina/dio/pull/1550).
