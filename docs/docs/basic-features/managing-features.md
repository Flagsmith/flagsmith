---
title: Managing Features
description: Feature Flags allow you to ship code and features before they are finished.
---

:::info Core Concepts
Flags in Flagsmith follow two key principles:
- They are **created and shared** at the Project level
- They can be **overridden** at the Environment level, per Identity, or per Segment
:::

## Flag Components

Each flag in Flagsmith consists of two main components:

1. **Flag State** - A required Boolean value that determines if the flag is ON (true) or OFF (false)

2. **Flag Value** (Optional) - Can be one of:
   - A String/Integer/Boolean value
   - A selected Multivariate value (String/Integer/Boolean)

You have the flexibility to use:
- Just the Flag State (Boolean)
- Just the Flag Value
- Both Flag State and Flag Value together

:::tip
If you only need a simple ON/OFF toggle, you can use just the Flag State and ignore the Flag Value entirely.
:::

:::caution Important Size Limit
The maximum size for String Values is **20,000 bytes**. Plan your string content accordingly.
:::

## Examples of Use

This allows you to use Flagsmith in the multiple ways:

- Showing and hiding features in your application. E.g. Controlling a new User Interface element within your application
  using the boolean `Flag State`
- Configuring environment variables/keys in your application. E.g. Setting the database URL for your API using the
  String `Flag Value`, or setting the Google Analytics API key in your front end.
- Configuring String values used within your application remotely. E.g. You might want to define different colour
  schemes for your application banner depending on the Environment.

If you provide a `Flag Value` to a flag, this will always be included and returned within the
[Flagsmith SDKS](/clients/rest/) and API, regardless of the boolean `Flag State`.

## Creating a new Feature Flag

You can create a new feature flag by going to the Flags page within any Environment and hitting the Create Feature
button.

Flags default to On (true) or Off (false). You can also optionally store and override String and Integer values. The
Flagsmith SDKs allow you to call both `hasFeature` as well as `getValue` on the same flag. These calls will retrieve
both the Boolean value as well as the String/Numerical value if specified. The SDKs generally return False/Null if the
flag is missing or the value is not set, but there are variations between different languages.

## Multi-Variate Flags

You can create a Multivariate Flag if you want the `Flag Value` to be one value out of a selection that you define. Each
Environment within a Project can then define and select which value to return based on this list. Multivariate Flags are
useful in 2 core use-cases:

1. You want to be able to control the `Flag Value` from a pre-selected list.
2. You want to run an A/B test. [Learn more here](/advanced-use/ab-testing.md).

Multi-Variate Flag values are defined as a "Control" and "Variations". The Control value is always sent as the Flag
Value when you get the Flags for the Environment without passing in a
[User Identity](/basic-features/managing-identities.md).

:::important

The Control and Variant weightings **_only_** come into effect if you are getting the Flags for a particular Identity.
If you are just retrieving the flags for an Environment without passing in an Identity, you will **_always_** receive
the Control value.

:::

If you are getting the Flags for an Identity, the Flagsmith engine will send the value based on the defined Weightings,
as specified within the Environment.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/multi-variate-flags.png"/></div>

In the screenshot above, roughly half our user population will receive the value `normal`, roughly one quarter (25%)
will receive `large` and roughly one quarter (25%) will receive `huge`. Note that you can use 100% as a weighting to
ensure all your users receive the same variant.

:::important

Multi Variate _values_ are defined at the Project level, but the _weightings_ are defined at the Environment level. Each
variate String Value will be the same amongst all Environments. Consequently, changing the _value_ of a variation in one
Environment will change that value for all the other Environments within the Project.

The _weightings_ of each variation, on the other hand, are defined at the Environment level. Changing a Variate
weighting in the `development` environment, for example, will not change the corresponding variation weighting in any
other Environments within the Project.

:::

### Multi-Variate Flag Use Cases

The primary use case for using Multi-Variate flags is to drive [A/B tests](/advanced-use/ab-testing.md).

### Custom fields

Optional or required custom fields can be defined when creating or updating features.
[Learn more](/advanced-use/custom-fields.md)
