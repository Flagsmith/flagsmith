---
title: Flagsmith Android/Kotlin SDK
sidebar_label: Android / Kotlin
description: Manage your Feature Flags and Remote Config in your Android applications.
slug: /clients/android
---

This SDK can be used for Android applications written in Kotlin. The source code for the client is available on
[GitHub](https://github.com/Flagsmith/flagsmith-kotlin-android-client/).

## Installation

### Gradle - App

In your project path `app/build.gradle` add a new dependence

```groovy
//flagsmith
implementation 'com.github.Flagsmith:flagsmith-kotlin-android-client:1.5.0'
```

You should be able to find the latest version in the
[releases section](https://github.com/Flagsmith/flagsmith-kotlin-android-client/releases) of the GitHub repository.

### Gradle - Project

In the new Gradle version 7+ update your `settings.gradle` file to include JitPack if you haven't already

```groovy
repositories {
    google()
    mavenCentral()

    maven { url "https://jitpack.io" }
}
```

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your Client-side Environment Key in the Environment
settings page.

## Initialization

### Within your Activity inside `onCreate()`

```kotlin
lateinit var flagsmith : Flagsmith

override fun onCreate(savedInstanceState: Bundle?) {
    initFlagsmith();
}

private fun initFlagsmith() {
    flagsmith = Flagsmith(environmentKey = FlagsmithConfigHelper.environmentDevelopmentKey, context = context)
}
```

## Custom configuration

The Flagsmith SDK has various parameters for initialisation. Most of these are optional, and allow you to configure the
Flagsmith SDK to your specific needs:

- `environmentKey` Take this API key from the Flagsmith dashboard and pass here
- `baseUrl` By default we'll connect to the Flagsmith backend, but if you self-host you can configure here
- `context` The current Context is required to use the Flagsmith Analytics functionality
- `enableAnalytics` Enable analytics - default true. Disable this if you'd like to avoid the use of Context
- `analyticsFlushPeriod` The period in seconds between attempts by the Flagsmith SDK to push analytic events to the
  server
- `enableRealtimeUpdates` Enable the SDK to receive updates to features in real time while the app is running
- `defaultFlags` Provide default flags the the SDK to ensure values are availble when no network connection can be made
- `cacheConfig` Disabled by default, but when enabled will allow Flagsmith to fall back to cached values when no network
  connection can be made
- `request / read / writeTimeoutSeconds` Fine-grained control of the HTTP timeouts used inside the Flagsmith SDK

## Flags

Now you are all set to retrieve feature flags from your project. To list and print all flags:

```kotlin
flagsmith.getFeatureFlags { result ->
    result.fold(
        onSuccess = { flagList ->
            Log.i("Flagsmith", "Current flags:")
            flagList.forEach { Log.i("Flagsmith", "- ${it.feature.name} - enabled: ${it.enabled} value: ${it.featureStateValue ?: "not set"}") }
        },
        onFailure = { err ->
            Log.e("Flagsmith", "Error getting feature flags", err)
        })
}
```

### Get Flag Object by `featureId`

To retrieve a feature flag boolean value by its name:

```kotlin
flagsmith.hasFeatureFlag(forFeatureId = "test_feature1") { result ->
    val isEnabled = result.getOrDefault(true)
    Log.i("Flagsmith", "test_feature1 is enabled? $isEnabled")
}
```

### Create a Trait for a user identity

```kotlin
flagsmith.setTrait(Trait(key = "set-from-client", value = "12345"), identity = "test@test.com") { result ->
    result.fold(
        onSuccess = { _ ->
            Log.i("Flagsmith", "Successfully set trait")

        },
        onFailure = { err ->
            Log.e("Flagsmith", "Error setting trait", err)
        })
}
```

### Get all Traits

To retrieve a trait for a particular identity as explained here
[Traits](../../basic-features/managing-identities.md#identity-traits)

```kotlin
flagsmith.getTraits(identity = "test@test.com") { result ->
    result.fold(
        onSuccess = { traits ->
            traits.forEach {
                Log.i("Flagsmith", "Trait - ${it.key} : ${it.traitValue}")
            }
        },
        onFailure = { err ->
            Log.e("Flagsmith", "Error getting traits", err)
        })
}
```

### Providing Default Flags

You can define default flag values when initialising the SDK. This ensures that your application works as intended in
the event that it cannot receive a response from our API.

```kotlin
val defaultFlags = listOf(
    Flag(
        feature = Feature(
            id = 345345L,
            name = "Flag 1",
            createdDate = "2023‐07‐07T09:07:16Z",
            description = "Flag 1 description",
            type = "CONFIG",
            defaultEnabled = true,
            initialValue = "true"
        ), enabled = true, featureStateValue = "value1"
    ),
    Flag(
        feature = Feature(
            id = 34345L,
            name = "Flag 2",
            createdDate = "2023‐07‐07T09:07:16Z",
            description = "Flag 2 description",
            type = "CONFIG",
            defaultEnabled = true,
            initialValue = "true"
        ), enabled = true, featureStateValue = "value2"
    ),
)

// Then pass these during initialisation:
flagsmith = Flagsmith(
    environmentKey = FlagsmithConfigHelper  environmentDevelopmentKey,
    defaultFlags = defaultFlags,
    context = context)

```

### Cache

By default, the cache is off. When turned on, Flagsmith will cache all flags returned by the API (to permanent storage),
and in case of a failed response, fall back on the cached values. The cache can be turned off or on during
initialisation:

```kotlin
flagsmith = Flagsmith(
    environmentKey = FlagsmithConfigHelper  environmentDevelopmentKey,
    cacheConfig = FlagsmithCacheConfig(enableCache = true)
    context = context)
```

You can also set a TTL for the cache (in seconds) for finer control:

```kotlin
FlagsmithCacheConfig (
    enableCache = true,
    cacheTTLSeconds = 3600L, // 1 hour
    val cacheSize = 1024L * 1024L, // 1 MB
)
```

## Override the default base URL

By default, the client uses a default configuration. You can override the configuration as follows. If you're also using
realtime flag updates in your hosted environment you'll also need to pass the eventSourceUrl in a similar fashion:

```kotlin
        flagsmith = Flagsmith(
            environmentKey = Helper.environmentDevelopmentKey,
            context = context,
            baseUrl = "https://hostedflagsmith.company.com/"),
            eventSourceUrl = "https://api.hostedflagsmith.company.com/"
```
