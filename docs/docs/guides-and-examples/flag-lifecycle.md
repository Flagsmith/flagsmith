---
title: Feature Flags Lifecycles
---

Feature Flags generally have two lifecycles:

1. Short-Lived Flags
2. Long-Lived Flags

Lets go over each type in detail.

## Short-Lived Flags

Short-lived flags are designed to be removed from your code and from Flagsmith at some point in the future. Their
typical lifecycle is normally something like:

1. Create flag in Flagsmith.
2. Add the flag to your application code.
3. Toggle the flag and/or apply Segment overrides to control your application behaviour.
4. Once you are finished with the flag, remove the flag from your codebase.
5. Deploy your application, so that there is no reference to the flag.
6. Remove the flag from Flagsmith.

Short lived flags are typically used for the following use-cases:

### Feature Roll-Outs

The most common use of flags in general is to decouple the deployment of a feature from it's release. When using a flag
to achieve this, you will generally remove the flag from your code and from Flagsmith once you are happy with the
feature and it is rolled out to your entire user population.

Once this is the case, there is no reason to have the flag exist either in Flagsmith or your code, hence it is
considered good practise to remove it from both.

### Experimentation

You can use Multi-variate flags to drive [A/B and multivariate tests](../advanced-use/ab-testing.md). Once your
experiment is complete, there is typically no need for the flag to remain, and hence it can be removed.

## Long-Lived Flags

Conversely, sometimes you will create flags that are long-lived - quite possibly for the lifetime of the application.
Here are a few use cases where this approach can be used.

### Kill Switches

There are often times where you need to be able remotely remove a feature, area of your application or sometimes the
application as a whole (in the event of a large deployment, for example). In these instances, flags can be used as 'kill
switches' to remove a feature altogether, or maybe to prevent users from using the application in the event of downtime.

Kill switches are generally long-lived; they often exist in the event of an unexpected event or error, and so they need
to be long-lived in case they need to be put to use.

### Feature Management Flags

You can make use of [Segments](../basic-features/segments.md) and Flags to control how different features are enabled or
disabled depending on the user. For example, you can send a Trait `plan` with the relevant user value (e.g. `scale-up`)
to Flagsmith, then create a Segment that defines all users on the `scale-up` plan. You can then show or hide features
based on this Segment and plan.

When employing feature flags in this manner, generally you would never remove this Flag or Segment, as you are using
them to drive platform features for the lifetime of the application.
