# Edge API

[The Flagsmith Architecture](/guides-and-examples/integration-approaches#flags-are-evaluated-server-side) is based
around a server-side flag engine. This comes with a number of benefits, but it can increase latency, especially when the
calls are being made from a location that is far from the EU; the location of our current API.

In order to solve this problem we have developed a Global Edge API. Our aim for this API is to serve all SDK requests
within 100 milliseconds, anywhere in the world. In order to achieve this, we are using the following AWS components.

## Enabling the Edge API

:::tip

The Edge API is currently in beta. If you want to join the beta programme, please connect with us in
[Discord](https://discord.gg/hFhxNtXzgm), via the chat widget at the bottom of this page or by emailing
support@flagsmith.com

:::

Once you have had your project added to the beta, all you will need to do is point your SDK to a new Flagsmith Edge API
URL. This URL will point to our edge Cloudfront CDN. That's it!

So for example, in the Java SDK we just add the `withApiUrl` line:

```java
FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
        .setApiKey("aaa"))
        .withApiUrl("https://edge.api.flagsmith.com/api/v1/")
        .build();
```

Check the docs for your language SDK on how to override the endpoint URL prefix.

## Current Caveats

Whilst in beta, there are some limitations to the platform. These are being worked on and will be in place when we put
the Edge API into production.

### Identities are only synced from Core to Edge API

If you cause a write to an Identity in our Core API, we will copy it to our Edge API data store. We will NOT copy data
in the opposite direction: writes to Edge will not be copied to Core.

### Increment and Decrement endpoints are deprecated

You probably didn't know these existed though, right?

### The API responses have been slimmed down

Our core API responses are quite verbose, and the SDKs ignore a lot of the fields they receive. We've taken the
opportunity to remove these additional, unused fields. This wont affect the SDKs but if you are using these values via
the REST API, things have changed. The list of removed fields is as follows:

```txt
trait.id
flag.feature.created_data
flag.feature.description
flag.feature.initial_value
flag.feature.default_enabled
flag.environment
flag.identity
flag.feature_segment
```

## How It Works

### Lambda@Edge

Our core [Rules Engine](https://github.com/Flagsmith/flagsmith-engine) has been factored out of our REST API. This
allows us to use it as a dependency within both the Flagsmith API, but also within a set of Lambda functions that
service SDK API calls. You can point your SDK clients to our global CDN `edge.api.flagsmith.com` which will serve your
request using a Lambda function running in an AWS data-centre near your client. This is how we reduce latency!

### DynamoDB Global Tables

We store state within our API - both related to the Environments for your Projects, but also for the Identities within
those Environments. Our Edge design sees us write this data through to DynamoDB global tables, which are replicated
globally.

Currently we are writing through Environment data only (see Caveat below) but we plan on writing through Identities
soon.

Our Lambda functions then connect to the nearest DynamoDB table to retrieve both Environment and Identity data.
