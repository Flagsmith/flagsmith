---
title: Segment Rule Operators
sidebar_label: Segment Rule Operators
---

import Tabs from '@theme/Tabs'; import TabItem from '@theme/TabItem';

Segment rule operators in Flagsmith allow you to define how trait values are compared when evaluating segment membership. Note that all operators are case-sensitive.

| Name                  | Description                                                                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Exactly Matches (=)` | Trait value is equal to the rule value                                                                                                                   |
| `Does not match (!=)` | Trait value is not equal to the rule value                                                                                                               |
| `% Split`             | Identity is in the percentage bucket. [Learn more](?operators=percent#operator-details)                                                                  |
| `>`                   | Trait value is greater than the rule value                                                                                                               |
| `>=`                  | Trait value is greater than or equal to the rule value                                                                                                   |
| `<`                   | Trait value is less than the rule value                                                                                                                  |
| `<=`                  | Trait value is less than or equal to the rule value                                                                                                      |
| `In`                  | Trait value is equal to any element in a comma-separated list (case-sensitive). [Learn more](?operators=in#operator-details)                             |
| `Contains`            | Rule value is a substring of the trait value                                                                                                             |
| `Does not contain`    | Rule value is not a substring of the trait value                                                                                                         |
| `Matches regex`       | Trait value matches the given regular expression                                                                                                         |
| `Is set`              | Trait value is set for the given identity and trait key                                                                                                  |
| `Is not set`          | Trait value is not set for the given identity and trait key                                                                                              |
| `SemVer`              | Trait value is compared against the rule value according to [Semantic Versioning](https://semver.org/). [Learn more](?operators=semver#operator-details) |

### Operator details

<Tabs groupId="operators" queryString>
<TabItem value="in" label="In">

The `In` operator enables you to match a trait value against a comma-separated list of values. For example, the segment rule value might read `21,682,8345`. This would match against a trait value of `682` but not against a trait value of `683` or `834`.

The `In` operator can be useful for building segments that represent a specific set of tenants in your application. For example, you could create a segment with the following rule: `tenant_id In tenant_1,tenant_2,tenant_3`

</TabItem>
<TabItem value="semver" label="SemVer">

[SemVer](https://semver.org/) operators compare semantic version values. Consider the following segment rule:

`version` `SemVer >=` `4.2.52`

This segment would include all users that have a `version` trait set to `4.2.52` or greater. For example, any of the following `version` values would match:

- `4.2.53`
- `4.10.0`
- `5.0.0`

Versions are compared as defined by the [Semantic Versioning specification](https://semver.org/#spec-item-11).

</TabItem>
<TabItem value="percent" label="Percentage Split">

Percentage Split is the only operator that does not require a trait. You can use it to drive [A/B tests](/advanced-use/ab-testing) and [staged feature rollouts](/guides-and-examples/staged-feature-rollouts#creating-staged-rollouts).

Percentage Split deterministically assigns a "bucket" to each identity solely based on its ID and not any traits, meaning that Segment overrides that use Percentage Split will always result in the same feature value for a given identity.

If you create a Segment with a single Percentage Split rule, Identities who are members of that split when the split value is set to, say, 10% will be guaranteed to also be in that split if it is changed to a value higher than 10%.

If the Percentage Split is reduced in value, some Identities will be removed from that Percentage Split to maintain the balance. The algorithm is fairly simple and good to understand – it is [described here](/guides-and-examples/staged-feature-rollouts#how-does-it-work).

</TabItem>
<TabItem value="modulo" label="Modulo">

This operator performs a [modulo operation](https://en.wikipedia.org/wiki/Modulo_operation), which returns the remainder of dividing a numeric trait value by a given divisor. The operator accepts rule value in the format `divisor|remainder`. For example:

`user_id` `%` `2|0`

This segment will include all identities having a `user_id` trait that is divisible by 2, i.e. even numbers. This is equivalent to the following expression in many programming languages:

`user_id % 2 == 0`

</TabItem>
</Tabs>

### Minimum SDK versions for local evaluation mode

When running in local evaluation mode, SDK clients evaluate segment rules locally, which means they must be updated to support the latest operators.

If an SDK client tries to evaluate a segment rule that has an unrecognised operator, that rule will silently evaluate to `false`. The table below lists the minimum required SDK version required by each operator:

|         | Modulo | In    |
| ------- | ------ | ----- |
| Python  | 2.3.0  | 3.3.0 |
| Java    | 5.1.0  | 7.1.0 |
| .NET    | 4.2.0  | 5.0.0 |
| Node.js | 2.4.0  | 2.5.0 |
| Ruby    | 3.1.0  | 3.2.0 |
| PHP     | 3.1.0  | 4.1.0 |
| Go      | 2.2.0  | 3.1.0 |
| Rust    | 0.2.0  | 1.3.0 |
| Elixir  | 1.1.0  | 2.0.0 |

## Limits

These are the default limits for segments and rules:

- 100 segments per project
- 100 segment overrides per environment
- 100 rules per segment override
- 1000 bytes per segment rule value

See the [documentation on System Limits](system-administration/system-limits.md) for more details.

## Custom fields

Optional or required custom fields can be defined when creating or updating segments. [Learn more](/advanced-use/custom-fields.md)
