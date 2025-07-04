---
title: Segments
sidebar_label: Segments
---

import Tabs from '@theme/Tabs'; import TabItem from '@theme/TabItem';

# Segments

A segment is a subset of [identities](/basic-features/managing-identities.md), defined by a set of rules that match
identity [traits](managing-identities.md#identity-traits). An identity always belongs to a single environment and can
belong to any number of segments.

Once you have defined a segment, you can create **segment overrides** for features within an environment. A segment
override allows you to control the state of a feature only for identities that belong to a specific segment. This is
similar to how [identity overrides](managing-identities.md#identity-overrides) let you control the state of features for
an explicit set of identities that is known in advance.

Because segments are driven by identity traits, your application must identify the user when retrieving flags in order
for segment overrides to be applied. If your user is not identified, no overrides will be applied and all flags will be
returned exactly how they are defined in the current environment.

Segments and segment overrides can be used to implement many scenarios. For example:

- Test features in production before they are released by overriding them only for internal users or a QA team
- Deliver features only to "power users" who have logged in a certain number of times, have used specific functionality
  within your application, or any combination of factors
- Force a group of users into a specific [A/B test](advanced-use/ab-testing.md) variation by overriding weightings on
  [multivariate flags](managing-features.md#multi-variate-flags)
- Override behaviour based on the [application version number](/guides-and-examples/mobile-app-versioning.md), e.g. by
  using the SemVer rule operators
- Control features based on the time of day, date, weekday, etc. by passing it as a trait when evaluating flags for an
  identity

## Security and privacy

The Flagsmith API to set user traits, e.g. the `setTraits` method from the JavaScript SDK, does not require
authentication or credentials. This means that users can change their own traits, which could be a security problem if
you are using segments for authorisation or access control. If you must use segments for access control, make sure to
disable the
["Persist traits when using client-side SDK keys" option](system-administration/security.md#preventing-client-sdks-from-setting-traits)
on every environment that needs it, and use server-side SDKs to set traits instead. You can still use client-side SDKs
to read traits and flags derived from segments in this case.

Segment names and definitions might include sensitive or proprietary information that you do not want to expose to your
users. Because of this, segments are transparent to applications and are not included in API responses when using
[remote evaluation mode](/clients#remote-evaluation).

Segment definitions _are_ served to clients running in [local evaluation mode](/clients#local-evaluation), as this
allows them to calculate segments without making requests to the Flagsmith API. This is only an implementation detail
and no segment information is exposed when retrieving flags using any SDK method.

## Creating project or feature-specific segments

Segments created from the Segments page of the Flagsmith dashboard can be used to override any feature within a single
project.

To create a segment override, click on a feature in a specific environment and go to the Segment Overrides tab.

If you need to create a segment that will only ever be used to override a single feature, you can create a
**feature-specific segment** by clicking on "Create Feature-Specific Segment" when creating a segment override.
Feature-specific segments are otherwise functionally identical to project segments. By default, feature-specific
segments are not shown in the Segments page, unless you enable the "Include Feature-Specific" option.

Once created, project segments cannot be changed into feature-specific segments or vice versa.

## Order of rules within segments

Segment rules are evaluated in order, i.e. from top to bottom when viewed in the Flagsmith dashboard.

For example, consider the following segment:

1. 10% percentage split
2. `is_subscriber = true`

This segment would first select 10% of _all_ identities, and then choose subscribers from that cohort. Instead, if we
used the opposite order:

1. `is_subscriber = true`
2. 10% percentage split

This would first select all subscriber identities, and then randomly choose 10% of them.

## Multiple segment overrides for one feature

If a feature has multiple segment overrides, they are evaluated in order, i.e. from top to bottom when viewed in the
Flagsmith dashboard. The first matching override will be used to determine the state of a feature for a given identity.

## Flag evaluation precedence

Identity overrides always take precedence over segment overrides. Simply put, the order of precedence when evaluating a
flag is:

1. Identity overrides
2. Segment overrides
3. Default value for the current environment

## Trait data types

Each individual trait value is always stored as one of the following data types:

- String
- Boolean
- Integer
- Float

Values in segment rules, on the other hand, are always stored as strings. When segment rules are evaluated, rule values
will be coerced to be the same type as the trait value. If the rule value cannot be coerced, that rule will evaluate as
false. This provides some flexibility if you ever need to change the data type of a trait, e.g. from boolean to string,
while maintaining backwards and forwards compatibility in your application.

For example, consider the following code using the JavaScript SDK:

```javascript
flagsmith.identify('example_user_1234');
flagsmith.setTrait('accepted_cookies', true);
```

The value of the `accepted_cookies` trait will be stored as a boolean for this identity. If you define a segment rule
like `accepted_cookies = true`, the rule value `true` is stored as a string. Because the `accepted_cookies` was stored
as a boolean for this identity, the segment engine will coerce the rule's string value into a boolean, and things will
work as expected.

Suppose later on you needed to store a third possible state for the trait `accepted_cookies`, for example if users can
partially accept cookies. Your application can start storing this trait as a string without needing to modify your
existing segment:

```javascript
flagsmith.setTrait('accepted_cookies', 'partial');
```

This would continue to work as expected for identities that already have this trait set as a string value. Always
storing the trait as a string would also work, for example:

```javascript
flagsmith.setTrait('accepted_cookies', 'true');
```

The following string trait values will evaluate to `true`:

- `"True"`
- `"true"`
- `"1"`

## What's next

- Learn more about [segment rule operators](./segment-rule-operators.md) 
- Learn about [targeting and rollouts](/flagsmith-concepts/targeting-and-rollouts.md) 
