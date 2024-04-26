---
title: Efficient API Usage
sidebar_label: Efficient API Usage
---

It is good engineering practise to reduce the frequency of API calls made from your applications to Flagsmith. There are
a number of reasons for this:

- Reducing network activity means your applications use less client resources like mobile device battery, CPU and
  network.
- You don't need to reflect state updates in your application as often.
- It saves you money! Whether you are self hosting or using our SaaS API, reducing API call volume costs you less.

## Client Side

### Getting Flags Once Per Session

The most common, most efficient workflow we have found with people using Flagsmith on the client side (browsers, mobile
apps etc) is the following:

1. The user opens the app for the first time, as an anonymous user.
2. The application loads, using Default Flag values as defined in code.
3. The application makes a request for the Flags for the Environment (_not_ the Identity as the user is still unknown at
   this stage).
4. The user logs into the application. A request is then made for the Identity Flags (along with any Traits for that
   Identity).
5. This data is then cached locally on the device and used for the duration of the user's session.
6. When the user reopens the app (for example, the following day) the cached values in the previous step are used. The
   application then re-requests the Identity flags (in case any flags have changed in the meantime) and caches the data.

### Setting Traits Efficiently

Every time a Trait as set via the SDK, they will make a request to the Flagsmith API with the Trait data and receive an
updated set of flags.

In order to reduce these calls, we recommend setting the full complement of traits in a single SDK call. There's more
info around achieving this in our [Javascript FAQ](/clients/javascript#faqs).

### Real Time Flag Updates

In our experience, most applications do not benefit a great deal from real time flag updates. In addition, and
especially with client-side flags, thought needs to be given to ensuring features/UI widgets don't appear/disappear in
real time due to flag changes.

That being said, there are use-cases for real time flags. Using our
[real-time flags service](/advanced-use/real-time-flags) negates the need to poll the API from the client SDK, which can
significantly reduce API usage.

## Server Side

### Local Evaluation Mode

The most efficient way of evaluating Flags on the Server is using
[Local Evaluation mode](/clients/overview#local-evaluation). There are
[some caveats](/clients/overview#local-evaluation), so please be aware of them!

### CDN Usage

There are 3 main API calls the Flagsmith SDK can make:

1. Get the [Environment Document](/clients/overview#the-environment-document) for
   [Local Evaluation mode](/clients/overview#local-evaluation).
2. Get the Flags for an Environment.
3. Get the Flags for an Identity.

Of these 3, the first two are candidates for caching. If your project can tolerate a longer period of time between
someone modifying a flag in Flagsmith and that flag change being reflected within the SDK, you can place a cache between
Flagsmith and your server side SDKs. The easiest way to do this is with a CDN, specifying the TTL to whatever you can
tolerate, and overriding the Flagsmith API URL within the SDK to point to your CDN.

Note that you almost certainly _don't_ want to cache the Get the Flags for an Identity.

### Edge Proxy

Using the [Edge Proxy](/advanced-use/edge-proxy) can significantly reduce API usage. A single instance of the Edge Proxy
makes one API request by default every 10 seconds to the Flagsmith API. With that request data it can then serve
potentially thousands of requests per second.

Consideration needs to be given to the caveats of running the Edge Proxy, but its deployment can have a dramatic effect
on reducing API call volume.
