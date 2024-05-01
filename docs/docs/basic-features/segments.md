---
description: Group your users based on a set of rules, then control Feature Flags and Remote Config for those groups.
---

import Tabs from '@theme/Tabs'; import TabItem from '@theme/TabItem';

# Managing Segments

Segments allow you to group your users based on a set of rules, and then control Feature Flags and Remote Config for
those groups. You can create a Segment and then override a Feature Flag state or Remote Config value for that segment of
users.

Segments for Flags and Config are overridden at the Environment level, meaning that different Environments can define
their own Segment overrides.

Segments **_only_** come into effect if you are getting the Flags for a particular Identity. If you are just retrieving
the flags for an Environment without passing in an Identity, your user will **_never_** be applied to a Segment as there
is no context to use.

:::tip

Segments are _not_ sent back to [Client-Side SDKs](/clients/overview#client-side-sdks). They are used to override flag
values within the dashboard, but they are never sent back to our
[Client-Side SDKs](https://docs.flagsmith.com/clients/overview#client-side-sdks) from the API.

They _are_ sent back to Server Side SDKs running in [Local Evaluation mode](/clients/overview#local-evaluation).

[Learn more about our architecture](/clients/overview#local-evaluation).

:::

## Example - Beta Users

:::important

Segment definitions can be defined at the **Project** or **Flag** level. **Project** level Segments are defined at the
Project level and can be used with any number of Flags within that Project. **Flag Specific** Segments can only affect
the Flag they are defined within.

:::

Let's say that you want all your team to automatically be defined as `Beta Users`. Right now, all your logged in users
are [identified](/basic-features/managing-identities.md) with their email address along with some other
[traits](/basic-features/managing-identities.md#identity-traits).

You can create a new Segment by going navigating to Segments and clicking the "Create Segment" button, call it
`Beta Users`, and define a single rule:

- `email_address` contains `@flagsmith.com`

Once the Segment has been defined, you can then associate that Segment with a specific Feature Flag. To do this, open
the Feature Flag that you want to connect the Segment to and navigate to the **Segment Overrides** tab. You then have
the option of connecting a Segment to the Feature. This then allows you to override the flag value for Users that are
within that Segment. If the Identified user is a member of that Segment, the flag will be overridden.

For all the Feature Flags that relate to Beta features, you can associate this `Beta Users` segment with each Flag, and
set the Flag value to `true` for that Segment. To do this, edit the Feature Flag and select the segment in the 'Segment
Overrides' drop down.

At this point, all users who log in with an email address that contains `@flagsmith.com` will have all Beta features
enabled.

Let's say that you then partner with another company who need access to all Beta features. You can then modify the
Segment rules:

- `email_address` contains `@flagsmith.com`
- `email_address` contains `@solidstategroup.com`

Now all users who log in with a `@solidstategroup.com` email address are automatically included in beta features.

## Feature-Specific Segments

You can also create Segments _within_ a Feature. This means that only that Feature can make use of that Segment. Feature
Specific Segments are useful when you know you will only need to use that Segment definition once. Go to the Feature,
then the Segment Overrides Tab, and click the "Create Feature-Specific Segment" button.

## Multi-Variate Values

If you are using [Multi-Variate Flag Values](managing-features.md#multi-variate-flags), you can also override the
individual value weightings as part of a Segment override.

## Rules Operators

The full set of Flagsmith rule operators are as follows:

| Name                   | Condition                                                                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Exactly Matches (==)` | Trait value is equal to segment value.                                                                                                                       |
| `Does Not Match (!=)`  | Trait value is not equal to segment value.                                                                                                                   |
| `% Split`              | Identity is in the percentage bucket. See [Percentage Split Operator](?operators=percent#operator-details).                                                  |
| `>`                    | Trait value is greater than segment value.                                                                                                                   |
| `>=`                   | Trait value is greater than or equal to segment value.                                                                                                       |
| `<`                    | Trait value is less than segment value.                                                                                                                      |
| `<=`                   | Trait value is less than or equal to segment value.                                                                                                          |
| `In`                   | Trait value is equal to one or more elements in a comma delimited list. See [The `In` operator](?operators=in#operator-details).                             |
| `Contains`             | Segment value is a substring of trait value.                                                                                                                 |
| `Does Not Contain`     | Segment value is not a substring of the trait value.                                                                                                         |
| `Matches Regex`        | Segment value, set to a valid Regex expression, is applied to trait value and matches it.                                                                    |
| `Is Set`               | Trait value is set for given identity and trait key.                                                                                                         |
| `Is Not Set`           | Trait value is not set for given identity and trait key.                                                                                                     |
| `SemVer >`             | Trait value is set to a newer SemVer-formatted version than segment value. See [SemVer-aware operators](?operators=semver#operator-details).                 |
| `SemVer >=`            | Trait value is set a newer SemVer-formatted version than segment value or equal to it. See [SemVer-aware operators](?operators=semver#operator-details).     |
| `SemVer <`             | Trait value is set to an older SemVer-formatted version than segment value. See [SemVer-aware operators](?operators=semver#operator-details).                |
| `SemVer <=`            | Trait value is set to an older SemVer-formatted version than segment value or equal to it. See [SemVer-aware operators](?operators=semver#operator-details). |

## Operator Details

<Tabs groupId="operators" queryString>
<TabItem value="in" label="In">

The `In` operator lets you match a Trait value against a comma-separated list of values. For example, the Segment rule
value might read `21,682,8345`. This would then match against a Trait value of `682` but not against a Trait value of
`683`.

The `In` operator can be useful when building Segments to match against tenancies within your application. Let's say you
wanted a Segment to evaluate as true for 5 different customer tenancies. Create a Segment rule where the `In` operator
matches all of those 5 customer tenancy ID's and no others. You can then create a Trait value for the Identity that
contains the tenancy ID of that user.

The `In` operator _is_ case sensitive when evaluating alphabetical characters.

:::important

Earlier SDK versions will not work in local evaluation mode if your environment has segments with the `In` operator
defined.

To keep local evaluation from breaking, please ensure you have your SDK versions updated before you add such segments to
your environment.

:::

These minimum SDK versions support segments with the `In` operator in
[local evaluation mode](/clients/overview#local-evaluation):

- Python SDK: `3.3.0+`
- Java SDK: `7.1.0+`
- .NET SDK: `5.0.0+`
- NodeJS SDK: `2.5.0+`
- Ruby SDK: `3.2.0+`
- PHP SDK: `4.1.0+`
- Go SDK: `3.1.0+`
- Rust SDK: `1.3.0+`
- Elixir SDK: `2.0.0+`

</TabItem>
<TabItem value="semver" label="SemVer">

The following [SemVer](https://semver.org/) operators are also available:

- `SemVer >`
- `SemVer >=`
- `SemVer <`
- `SemVer <=`

For example, if you are using the SemVer system to version your application, you can store the version as a `Trait` in
Flagsmith and then create a rule that looks like, for example:

`version` `SemVer >=` `4.2.52`

This Segment rule will include all users running version `4.2.52` or greater of your application.

</TabItem>
<TabItem value="percent" label="Percentage Split">

:::important

The percentage split operator **_only_** comes into effect if you are getting the Flags for a particular Identity. If
you are just retrieving the flags for an Environment without passing in an Identity, your user will **_never_** be
included in the percentage split segment.

:::

This is the only operator that does not require a Trait. You can use the percentage split operator to drive
[A/B tests](/advanced-use/ab-testing) and
[staged feature rollouts](/guides-and-examples/staged-feature-rollouts#creating-staged-rollouts).

When you use a percentage split operator in a segment that is overriding a feature, each user will be placed into the
same 'bucket' whenever that feature is evaluated for that user, and hence they will always receive the same value.
Different users will receive different values depending on your split percentage.

</TabItem>
<TabItem value="modulo" label="Modulo">

:::important

Earlier SDK versions will not work in local evaluation mode if your environment has segments with the `Modulo` operator
defined.

To keep local evaluation from breaking, please ensure you have your SDK versions updated before you add such segments to
your environment.

:::

This operator performs [modulo operation](https://en.wikipedia.org/wiki/Modulo_operation). This operator accepts rule
value in `divisor|remainder` format and is applicable for Traits having `integer` or `float` values. For example:

`userId` `%` `2|0`

This segment rule will include all identities having `int` or `float` `userId` trait and having a remainder equal to 0
after being divided by 2.

`userId % 2 == 0`

These minimum SDK versions support segments with the `Modulo` operator in
[local evaluation mode](/clients/overview#local-evaluation):

- Python SDK: `2.3.0+`
- Java SDK: `5.1.0+`
- .NET SDK: `4.2.0+`
- NodeJS SDK: `2.4.0+`
- Ruby SDK: `3.1.0+`
- PHP SDK: `3.1.0+`
- Go SDK: `2.2.0+`
- Rust SDK: `0.2.0+`
- Elixir SDK: `1.1.0+`

</TabItem>
</Tabs>

## Rule Typing

When you store Trait values against an Identity, they are stored in our API with an associated type:

- String
- Boolean
- Integer

When you define a Segment rule, the value is stored as a String. When the Segment engine runs, the rule value will be
coerced into the type of the Trait value. Here are some examples.

You store a Trait, here with an example in Javascript:

```javascript
flagsmith.identify('flagsmith_sample_user');
flagsmith.setTrait('accepted_cookies', true);
```

So here you are storing a native `boolean` value against the Identity. You can then define a Segment rule, e.g.
`accepted_cookies=true`. Because the Identity trait named `accepted_cookies` is a boolean, the Segment engine will
coerce the string value from `accepted_cookies=true` into a boolean, and things will work as expected.

If you were to then change the trait value to a String at a later point the Segment engine will continue to work,
because the Identity's Trait value has been stored as a String

```javascript
flagsmith.setTrait('accepted_cookies', 'true');
```

For evaluating booleans, we evaluate the following 'truthy' String values as `true`:

- `True`
- `true`
- `1`

## Segment Rule Ordering

Flagsmith evaluates the conditions of a Segment in the order they are defined. This can affect how things are processed
and should be considered when creating your Segment rules.

For example, let’s say I have this segment:

1. Percentage Split = 10%
2. isSubscriber = true

This Segment would randomly select 10% of _all_ Identities first and then filter the subscribers. You could also define
the Segment rules the other way around:

1. isSubscriber = true
2. Percentage Split = 10%

This definition makes the isSubscriber check first, and the Split condition is second, operating purely on the pool of
subscribed users.

## Feature Flag and Remote Config Precedence

Feature Flag states and Remote Config values can be defined in 3 different places:

1. The default Flag/Config value itself
2. The Segment associated with the Flag/Config
3. Overridden at an Identity level

For example, a Feature Flag `Show Paypal Checkout` could be set to `false` on the Flag itself, `true` in the Beta Users
segment, and then overridden as `false` for a specific Identity.

In order to deal with this situation, there is an order of priority:

1. If the Identity has an override value, this is returned ahead of Segments and Flags/Config
2. If there's no Identity override, the Segment is checked and returned if valid
3. If no Identity or Segment overrides the value, the default Flag/Config value is used

More simply, the order of precedence is:

1. Identity
2. Segment
3. Flag
