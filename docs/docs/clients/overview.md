---
description: Manage your Feature Flags and Remote Config in your REST APIs.
sidebar_label: Overview
sidebar_position: 1
---

# SDKs Overview

Flagsmith ships with SDKs for a bunch of different programming languages. We also have a [REST API](rest.md) that you
can use if you want to consume the API directly.

The SDKs are split into two different types: **Client-side** and **Server-side** sdks. These SDKs have different methods
of operation due to the differences in their operating environment.

:::tip

**Environment Keys** come in two different types: Client-side and Server-side keys. Make sure you use the correct key
depending on the SDK you are using.

:::

## Client-side SDKS

Client-side SDKs run in web browsers or on mobile devices. These runtimes execute within _untrusted environments_.
Anyone using the Javascript SDK in a web browser, for example, can find the Client-side SDK, create a new Identity, look
at their flags and
[potentially write Traits to the Identity](/system-administration/security#preventing-client-sdks-from-setting-traits).

Client-side SDKs are also limited to the
[types of data that they have access to](/guides-and-examples/integration-approaches#segment-and-targeting-rules-are-not-leaked-to-the-client).

Client-side Environment keys are designed to be shared publicly, for example in your HTML/JS code that is sent to a web
browser.

Client-side SDKs hit our [Edge API](../advanced-use/edge-api.md) directly to retrieve their flags.

Read more about our Client-Side SDKs for your language/platform:

- [Javascript](/clients/javascript)
- [Android/Kotlin](/clients/android)
- [Flutter](/clients/flutter)
- [iOS/Swift](/clients/ios)
- [React & React Native](/clients/react)
- [Next.js, Svelte and SSR](/clients/next-ssr)

## Server-side SDKs

[Server-side SDKs](/clients/server-side.md) run within _trusted environments_ - typically the server infrastructure that
you have control over. Because of this you need to should not share your Server-side Environment keys publicly - they
should be treated as secrets.

:::tip

The Server Side SDKs can operate in 2 different modes:

1. `Remote Evaluation`
2. `Local Evaluation`

It's important to understand which mode is right for your use case, and what the pros and cons of each one are. This is
detailed below.

:::

### 1 - Remote Evaluation

In this mode, every time the SDK needs to get Flags, it will make a request to the Flagsmith API to get the Flags for
the particular request.

![Remote Evaluation Diagram](/img/sdk-remote-evaluation.svg)

`Remote Evaluation` is the default mode; initialise the SDK and you will be running in `Remote Evaluation` mode.

This is the same way that the [Client Side SDKs](#client-side-sdks) work.

### 2 - Local Evaluation

In this mode, all flag values are calculated locally, on your server. The Flagsmith SDK includes an implementation of
the Flag Engine, and the engine runs within your server environment within the Flagsmith SDK.

![Local Evaluation Diagram](/img/sdk-local-evaluation.svg)

You have to configure the SDK to run in `Local Evaluation` mode. See the
[SDK configuration options](server-side.md#configuring-the-sdk) for details on how to do that in your particular
language.

When the SDK is initialised in `Local Evaluation` mode, it will grab the entire set of details about the Environment
from the Flagsmith API. This will include all the Flags, Flag values, Segment rules, Segment overrides etc for that
Environment. This full complement of data about the Environment enables the Flagsmith SDK to run the Flag Engine
_locally_ and _natively_ within your server infrastructure.

The benefits to doing this are mainly one of latency and performance. Your server side code does not need to hit the
Flagsmith API each time a user requests their flags - the flags can be computed locally. Hence it does not need to block
and wait for a response back from the Flagsmith API.

:::tip

The SDK has to request all of the data about an Environment in order to run. Because some of this data could be
sensitive (for example, your Segment Rules), the SDK requires a specific `Server-side Environment Key`. This is
different to the regular `Client-side Environment Key`. The `Server-side Environment Key` should _not_ be shared, and
should be considered sensitive data.

:::

In order to keep their Environment data up-to-date, SDKs running in `Local Evaluation` mode will poll the Flagsmith API
regularly and update their local Environment data with any changes from the Flagsmith API. By default the SDK will poll
the Flagsmith every `60` seconds; this rate is configurable within each SDK.

It's important to understand the [pros and cons](#pros-cons-and-caveats) for running `Local Evaluation`.

### Client Side SDKs

All our Client Side SDKs run in `Remote Evaluation` mode only; they cannot run in `Local Evaluation mode`. The reason
for this is down to data sensitivity. Because some of this data could be sensitive (for example, your Segment Rules), we
only allow Client Side SDKs to run in `Remote Evaluation` mode.

:::info

Because Clients are almost always operating remotely from your server infrastructure, there is little benefit to them
running in `Local Evaluation` mode.

:::

## Pros, Cons and Caveats

### Remote Evaluation Mode

- Identities are persisted within the Flagsmith Datastore.
- Identity overrides specified within the Dashboard.
- All Integrations work as designed.

### Local Evaluation Mode

- Identities are _not_ sent to the API and so are not persisted in the datastore.
- Because Local mode does not connect to the datastore for each Flag request, it is not able to read the Trait data of
  Identities from the API. This means that you have to provide the full complement of Traits when requesting the Flags
  for a particular Identity. Our SDKs all provide relevant methods to achieve this.
- [Identity overrides](../basic-features/managing-identities#identity-overrides) do not operate at all.
- Analytics-based Integrations do not run.

The benefit of running in Local Evaluation mode is that you can process flag evaluations much more efficiently as they
are all computed locally.

:::tip

In circumstances where you need to target a specific identity, you can do this by creating a segment to target that
specific user and subsequently adding a segment override for that segment.

:::
