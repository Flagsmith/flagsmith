---
title: Identities
sidebar_label: Identities
sidebar_position: 4
---

Feature flags are great, but they can be a very blunt tool, only allowing you to enable or disable flags across your entire user base. In order to target users more precisely, and to be able to perform [staged feature roll-outs](/managing-flags/rollout/rollout-by-percentage) or [A/B and multivariate tests](/experimentation-ab-testing), you need to _identify your users_.

Identities are created within Flagsmith automatically the first time they are identified from your client SDKs. Generally, you would make a call to identify a user with a unique string or identifier whenever they log into your application or site. The SDK will then send an API message to the Flagsmith API, with the relevant identity information.

:::tip

The SDK part of the Flagsmith API is public by design; the environment key is intended to be public. When identifying users, it is important to use an identity value that is not easy to guess. For example, if you used an incrementing integer to identify your users, it would be trivial to request identities by enumerating this integer. This would effectively provide public access to any user traits that are associated with users.

We strongly recommend using an unguessable, unidentifiable identity key, such as a [GUID](https://en.wikipedia.org/wiki/Universally_unique_identifier), when identifying your users, to prevent unintentionally leaking identity trait data.

:::

## Identity Overrides

Once you have uniquely identified a user, you can then override features for that user from your environment defaults. For example, you've pushed a feature into production, but the relevant feature flag is still hiding that feature from all of your users. You can now override that flag for your own user, and test that feature. Once you are happy with everything, you can roll that feature out to all of your users by enabling the flag itself.

Identities are specific and individual for each environment within your project. For example, joe@yourwebsite.com would be a different identity in your development environment to the one in production, and they can have different features enabled for each environment.

## Identity Feature Flags

By default, identities receive the default flags for their environment. The main use-case for identities is to be able to override flags and configs on a per-identity basis. You can do this by navigating to the users page, finding the user
and modifying their flags.

## Identity Traits

You can also use Flagsmith to store 'traits' against identities. traits are key/value pairs that are associated with individual identities for a particular environment. traits have two purposes outlined below, but the main use case is to drive [segments](./segments).

:::important

The maximum size of each individual trait value is **_2000 bytes_**. You cannot store more data than that in a single trait, and the API will return a 500 error if you try to do so.

:::

### Using Traits to Drive Segments

Let's say you are working on a mobile app, and you want to control a feature based on the version of the application that the identity is using. When you integrate the Flagsmith SDK, you would pass the application version number to the Flagsmith platform as a trait key/value pair:

```javascript
const identifier = "user_512356";
const traits = {
  app_version: YourApplication.getVersion()
}

const flags = flagsmith.getIdentityFlags(identifier, traits);
```

Here we are setting the trait key `app_version` with the value of `YourApplication.getVersion()`.You can now create a [segment](./segments) that is based on the application version and manage features based on the application version.

Traits are completely free-form. You can store any number of traits, with any relevant information you see fit, in the platform and then use segments to control features based on these trait values.

## Identity and Trait Storage

Identities are persisted within the Flagsmith platform, along with any traits that have been assigned to them. When flags are evaluated for an identity, the full complement of traits stored within the platform are used, even if they were not all sent as part of the request.

This can be useful if, at runtime, your application does not have all the relevant trait data available for that particular identity; any traits provided will be combined with the traits stored within Flagsmith before the evaluation engine runs.

There are some [exceptions to this rule](/integrating-with-flagsmith/sdks/server-side) with Server-side SDKs running in local evaluation mode.

:::info

Note that, when using our SaaS platform, there might be a short delay from the initial request to write or update traits for an identity and them being used in subsequent evaluations.

:::

### Using Traits as a Data-store

Traits can also be used to store additional data about your users that would be cumbersome to store within your application. Some possible uses for traits could be:

- Storing whether the user has accepted a new set of terms and conditions.
- Storing the last viewed page of the application so that you can resume the users place later, across any device.

Generally if they are lower-value pieces of information about your user, it might be simpler/easier to store them in Flagsmith rather than in your core application.

Traits are stored natively as either numbers, strings or booleans.

## Traits Powering Segments

Traits can be used within your application, but they can also be used to power [segments](/flagsmith-concepts/segments).

## Trait Value Data Types

:::tip

You can remove a trait by sending `null` as the trait value.

:::

Trait values can be stored as one of four different data types:

- Boolean.
- String (max length 2000 bytes).
- Int (32 bit signed).
- Float (typically has a range of around 1E-307 to 1E+308 with a precision of at least 15 digits).

If you need to store 64 bit integers or very high precision floats we suggest storing them as strings and then doing the type conversion within the SDK.

## Bulk Uploading Identities and Traits

Identities are lazily created within Flagsmith. There might be instances where you want to push identity and trait data into the platform outside of a user session. We have [bulk upload API endpoints](/edge-api/bulk-insert-identities-update) for this.

For more information, see:

- [Managing identities](/flagsmith-concepts/identities).

