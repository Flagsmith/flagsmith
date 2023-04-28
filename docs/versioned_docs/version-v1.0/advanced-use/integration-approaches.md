---
title: Integration Approaches
---

We have put a lot of work into making the Flagsmith API fast, stable, reliable and fault tolerant. That being said,
there are some simple techniques that can be used to enhance things further and provide the best experience possible to
your users.

## SDK Flag endpoints are public

The API endpoints that our SDKs make calls to are all public. Your Environment API key should also be considered public.
Think if it in the same way you would a Google Analytics key.

## Flags are evaluated Server Side

Flagsmith is different to some other feature flag providers in that we evaluate your flag rules on our server. There are
some advantages to this approach:

### Segment and Targeting rules are not leaked to the client

If flags are evaluated within the SDK, the entire set of rules for targeting users based on Segments etc need to be sent
to the client. Given these endpoints are public by default, we think this is a leak of potentially sensitive
information. We think the best place for your flags to be evaluated is on our server.

### You can get your flags with a single HTTP GET

You don't need to run a set of complicated rule evaluations to get your flags. Just hit our endpoint and you get your
flags. You won't receive any information on Segments or rollout rules, and this is by design. If you want to run your
own HTTP client within your application its just a simple HTTP GET and you're good.

### Our SDKs are super-lightweight

We have designed our SDKs with minimal dependencies. Because we don't have to do any rule evaluation on the client, we
can keep the codebase for our SDKs slimmed down and without a bunch of dependencies you don't want.

## Sane Defaults

Whether your application is a mobile app or a server side rendered web platform, building with sane and safe flag
defaults is a good idea. There are two good ways to implement this practice.

### Hard Coded Defaults

Storing flag defaults in your code is the simplest way to achieve this. For example, in Java you could do something like
this:

```java
    public static boolean FF_FREEZE_DELINQUENT_ACCOUNTS = false;
    public static boolean FF_KYC_BUTTON = true;
    public static int FF_TWILIO_IMPORT_DAYS_TO_PROCESS = 45;
    public static boolean FF_YOTI_INCLUDE_LIVENESS = true;
    public static String FF_YOTI_UPLOAD_TYPE = "CAMERA";

    public static void setup() {

    FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
            .setApiKey(Play.configuration.getProperty("flagsmith.apikey"))
            .build();

    FF_FREEZE_DELINQUENT_ACCOUNTS = flagsmithClient.hasFeatureFlag("freeze_delinquent_accounts");
    FF_KYC_BUTTON = flagsmithClient.hasFeatureFlag("kyc_button");
    FF_YOTI_INCLUDE_LIVENESS = flagsmithClient.hasFeatureFlag("yoti_include_liveness");
    FF_YOTI_UPLOAD_TYPE = flagsmithClient.getFeatureFlagValue("yoti_upload_type");
```

That way, if for whatever reason the Flagsmith client is not able to reach the API, and times out, your application will
be able to function with sane default values.

### Build Time Flag Retrieval

A more advanced technique is to grab the Flag defaults from the Flagsmith API at build time and include them on your
application build. The steps for this might look something like this:

1. Push your code to your git repository.
2. An automated build pipeline is triggered.
3. One stage of the pipeline is to grab the current default flag states from the `/flags` endpoint and store the JSON
   response within your application build.
4. Upon startup of your application, read the JSON file is embedded within your application first to get sane default
   flags and config.
5. Asynchronously call the Flagsmith API to get the most recent Flag and Config values.

## Caching Flags Locally

This approach depends on whether your application has an ability to persist data to the host OS during runtime. Locally
caching flags within your application environment ensures that you can subsequently start your application without
having to block for a call to the Flagsmith API. A common workflow would then be:

1. Build your application with sane defaults.
2. Start your app, using the sane defaults, and asynchronously call the Flagsmith API to retrieve up-to-date Flags.
3. Once the up-to-date Flags are retrieved, store them locally.
4. On subsequent app launches, check local storage to see if any flags are available. If they are, load them
   immediately.
5. Asynchronously call the Flagsmith API to retrieve the up-to-date Flags.

The official [Javascript Client](/clients/javascript/) offers optional caching built in to the SDK.

## Caching Flags on a Server

When running the Flagsmith SDK within a Server environment, it is difficult for the SDK to ascertain what sort of
caching infrastructure is available to it. For this reason, caching flags in a Server Environment needs to be integrated
by hand. However, it's pretty simple!

1. When a server starts up, get the Flags from the Flagsmith API. They will now be in memory within the server runtime.
2. If you have caching infrastructure available (for example, memcache, redis etc), you can then store the flags for
   that environment within your caching infrastructure.
3. You can set up a [Web Hook](/advanced-use/system-administration.md#web-hooks) within Flagsmith that sends flag change
   events to your server infrastructure.
4. Write an API endpoint within your infrastructure that receives flag change events and stores then in your local
   cache.
5. You can now rely on your local cache to get up to date flags.
