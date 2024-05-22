# Real-Time Flags

:::tip

Real-time Flags are currently part of our SaaS Enterprise plans.

:::

## Overview

Real-time flags allow you to stream flag changes from Flagsmith downstream to connected clients.

## How it works

:::info

You need to enable the realtime listener in the Flagsmith SDK. Please check the docs for your SDK language on how to do
this.

:::

Our SDK will make a long-lived request (actually a
[Server Sent Event](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)), to
our real-time infrastructure. This connection will remain open for the duration of the SDK session, listening for events
from our API.

When an Environment is updated in some way, either via the Flagsmith dashboard or our API, all the clients connected to
that Environment stream will receive a message (actually an epoch timestamp) that alerts them to refresh their flags,
which they will go ahead and do.

It is then up to you, as part of the SDK integration, to reflect that new flag state within your application.

## Pricing

Real-time flags are included within the Scale-Up and Enterprise plans.

## SDK support

We are working to build out support for all our SDKs. We are going to prioritise client-side SDKs over server-side SDKs
but are happy to take pull requests!

### Client Side

| Language       | Support |
| -------------- | ------- |
| Javascript     | ✅      |
| iOS/Swift      | ❌      |
| Android/Kotlin | ❌      |
| Dart/Flutter   | ❌      |

### Server Side

| Language | Support |
| -------- | ------- |
| Node.js  | ❌      |
| Java     | ❌      |
| .Net     | ❌      |
| Python   | ❌      |
| Ruby     | ❌      |
| Rust     | ❌      |
| Go       | ❌      |
| Elixir   | ❌      |

## Things you should know

- Per-identity overrides do not trigger an update
- Identity Trait updates do not trigger an update

## How it works under the hood

When realtime streaming is enabled within the SDK, the client will try to connect to:
`eventSourceUrl + "sse/environments/" + environmentID + "/stream"`. The streaming services is built on top of
[Server Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events), _not_ Websockets!

By default, this `eventSourceUrl` is set to `https://realtime.flagsmith.com/`.

Every time flags are fetched (via identify, get flags, set traits etc) via the REST API, we update an epoch timestamp
internally within the SDK, storing how fresh the flags are.

Whilst connected to the streaming service, the client will receive a new epoch timestamp event if the Flagsmith
Environment state has changed. If that epoch timestamp value is greater (as in more recent) than our internal timestamp
we refetch the flags.
