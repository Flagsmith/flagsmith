---
description: Group your users based on a set of rules, then control Feature Flags and Remote Config for those groups.
---

# Managing Segments

Segments allow you to group your users based on a set of rules, and then control Feature Flags and Remote Config for
those groups. You can create a Segment and then override a Feature Flag state or Remote Config value for that segment of
users.

:::important

Segment definitions are shared amongst your Project's Environments. If you modify a Segment in one Environment, that
change will reflect in all the Environments for that Project.

:::

Segments for Flags and Config are overridden at the Environment level, meaning that different Environments can define
their own Segment overrides.

:::tip

Segments are _not_ sent back to client SDKs. They are used to override flag values within the dashboard, but they are
never sent back to our SDKs from the API.
[Learn more about our architecture](/guides-and-examples/integration-approaches#flags-are-evaluated-server-side).

:::

## Example - Beta Users

Let's say that you want all your team to automatically be defined as `Beta Users`. Right now, all your logged in users
are [identified](/basic-features/managing-identities.md) with their email address along with some other
[traits](/basic-features/managing-identities.md#identity-traits).

You create a new Segment, call it `Beta Users`, and define a single rule:

- `email_address` contains `@flagsmith.com`

![Image](/img/edit-segment.png)

Once the Segment has been defined, you can then associate that Segment with a specific Feature Flag. To do this, edit
the Feature Flag that you want to connect our Segment to. You then have the option of connecting a Segment to the
Feature. If the Identified user is a member of that Segment, the flag will be overridden.

![Image](/img/edit-feature-with-segment.png)

For all the Feature Flags that relate to Beta features, you can associate this `Beta Users` segment with each Flag, and
set the Flag value to `true` for that Segment. To do this, edit the Feature Flag and select the segment in the 'Segment
Overrides' drop down.

At this point, all users who log in with an email address that contains `@flagsmith.com` will have all Beta features
enabled.

Let's say that you then partner with another company who need access to all Beta features. You can then simply modify
the Segment rules:

- `email_address` contains `@flagsmith.com`
- `email_address` contains `@solidstategroup.com`

Now all users who log in with a `@solidstategroup.com` email address are automatically included in beta features.

## Rules Operators

The full set of Flagsmith rule operators are as follows:

- `Exactly Matches (=)`
- `Does Not Match (!=)`
- `% Split`
- `>`
- `>=`
- `<`
- `<=`
- `Contains`
- `Does Not Contain`
- `Matches Regex`

All of the operators act as you would expect. Some of the operators also have special powers!

### SemVer-aware operators

The following [SemVer](https://semver.org/) operators are also available:

- `SemVer >`
- `SemVer >=`
- `SemVer <`
- `SemVer <=`

For example, if you are using the SemVer system to version your application, you can store the version as a `Trait` in
Flagsmith and then create a rule that looks like, for example:

`version` `SemVer >=` `4.2.52`

This Segment rule will include all users running version `4.2.52` or greater of your application.

### Percentage Split Operator

:::important

The percentage split operator **_only_** comes into effect if you are getting the Flags for a particular Identity. If
you are just retrieving the flags for an Environment without passing in an Identity, your user will **_never_** be
included in the percentage split segment.

:::

This is the only operator that does not require a Trait. You can use the percentage split operator to drive
[A/B tests](/advanced-use/ab-testing) and
[staged feature rollouts](/guides-and-examples/staged-feature-rollouts#creating-staged-rollouts).

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
