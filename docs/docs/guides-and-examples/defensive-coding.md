---
title: Defensive Coding and Designing for Failure
sidebar_label: Defensive Coding
---

Introducing Feature Flags and Remote Config to your applications can provide a wealth of benefits, but there are also a
few drawbacks. Fortunately, the majority of these can be avoided through [defensive coding](#defensive-coding) and
sensible approaches to default flags.

In addition to the approaches you can take integrating our SDKs, there are a number of
[Design for Failure](#designing-for-failure) concepts that are built into the platform architecture to ensure that
Flagsmith provides a reliable, dependable solution.

## Defensive Coding

### Don't expect a 200 response from the Flagsmith API

First up - we care deeply about our [SaaS uptime and stability](https://flagsmith.statuspage.io/). Whilst no one has
100% uptime, in our experience there are numerous situations where your application is unable to get a response from our
API:

- They are using a mobile device, open your app, and step into a lift.
- They are using a web application in a hotel that has the craziest DNS setup you have ever seen.
- As above but for TLS certificates.
- They are running a DNS blocker that has over-zealous blacklists.

The list goes on and on, but the bottom line is that whilst our API being down is extremely unlikely, you cannot rely on
200's from our API in 100% of cases.

So with that in mind, here are some rules you can follow to avoid any issues stemming from the above.

### Don't block your application waiting on our response

The solution here really depends on which of our SDKs you are using. By default our Client SDKs will not block your main
application thread, and are designed to work around an asynchronous callback model.

Where our Server Side SDKs are being used, it really depends on if you are using them in
[local or remote evaluation mode](/clients/overview#networking-model). When running in local evaluation mode, once the
SDKs have received a response from the API with the Environment related data, they will keep that data in memory. In the
event of the SDKs then not receiving an update, they will continue to function.

In the event that the SDKs aren't able to contact the API at all, they will time out and resort to
[Default flags](#progressively-enhance-your-application-with-default-flags). When running in remote evaluation mode, you
will need to decide what the best approach is based on your particular application. Again,
[Default flags](#progressively-enhance-your-application-with-default-flags) can help here.

### Progressively enhance your application with default flags

The most effective way of dealing with these issues is to provide a sane set of default values for _all of your flags_.
The Flagsmith SDKs all have provision for specifying default values for both flag boolean and flag text values. We
strongly recommend setting defaults for all of your flags as a matter of routine.

Your application should operate in a default, safe mode and its behaviour should only be modified or enhanced with flags
on receiving an API response.

### Cache flags where possible

Our Javascript SDK has the capability of caching the last received flags in the localStorage of the user's browser. When
the browser starts a new session, the last cached flags will be used while waiting for a response from the API for a
fresh set of flags. This pattern helps if the browser never receives a response from the API.

## Designing for Failure

### The Edge API

When our SDKs request their flags, they will make requests to our [Edge API](/advanced-use/edge-api.md). This
infrastructure is serverless both at the compute and data-store, as well as being replicated across eight AWS regions.
We also provide latency based routing and regional fault tolerance.

What this means is that your application will be served by the nearest region to the request. In addition to this, in
the event of the failure of an entire AWS region, requests will automatically be routed to the next nearest region.

### Caching, Performant SDKs

Our client-side SDKs will always remember their last known flags and use these in the event that they cannot reach our
API; for example if they are on a mobile device set to flight mode.

In addition to this, by default our client-sde SDKs will only make a network call when they are initialised. Subsequent
requests for flag evaluation will happen locally in memory in fractions of a millisecond.

### Server side SDKs and local evaluation mode

If you need sub-millisecond latency for end-to-end flag evaluation, for example in the event that you are running a
multi-variate test on a landing page of your website, you can employ one of our Server Side SDKs running in
[local evaluation mode](/clients/overview#local-evaluation) mode. This will provide sub-millisecond latency of the
entire flag evaluation rules engine, running locally within your server infrastructure, allowing you to run multivariate
tests with zero latency impact.

### No proxy-server required

We do not require you to run any infrastructure whatsoever to run our platform. There are no relays, proxies, caches or
CDNs in between your client request and our API.

We do have an [Edge Proxy](/advanced-use/edge-proxy) if required, but it is entirely optional.

### Bring your own CDN or DNS if you wish

Because we don't do any caching, you are free to add your own reverse proxy into the architecture if you wish. Customers
often do this to provide an additional layer of security (for example, only allowing authenticated clients to get their
flags). They also do this to ensure that requests from their application don't make requests to a third party domain,
for example by setting up their own DNS namespace for our API.
