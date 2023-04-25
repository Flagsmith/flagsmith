---
title: Mobile App Versioning
---

## The Problem

Feature Flags really come into their own when managing the features of a mobile application. If you ship a bug in your
mobile app, there is a significant time delay in getting a fix onto your user's device:

1. You have to wait for App/Play Store approval (although this time period has got much better in recent years)
2. Once your new app version is live, you then have to wait for your users to upgrade their application, which could
   take weeks or even months.

Combined, these two problems can cause real headaches if you ship a bug. Feature flags to the rescue...

## The Solution

We're going to create a Segment of affected users, and override (in this case, disable) the affected feature from _just
the affected users_ of our application altogether. Here's how we go about it.

### 1. Put Features behind Flags

It sounds obvious, but if you don't wrap features in feature flags, you lose the ability to control them remotely. Make
it a part of your routine to wrap new features/code in flags so you can start managing them remotely.

### 2. Start telling Flagsmith about the Device and Application Version

Using [Identities and Traits](/basic-features/managing-identities.md), make sure you are transmitting data about your
device type and version to Flagsmith. We recommend using the following Traits:

- Platform (iOS or Android)
- Platform Version (e.g. Android 11, iOS 14)
- Your Application Version (this would be the version number you ship your app as - generally the one that shows up in
  the App/Play Store)

### 3. Track down your bug

When you inevitably do ship a bug (don't worry; we've all been there!), and the bug reports start rolling in, try and
rapidly isolate exactly what subset of devices are affected:

- Is it just iOS devices running the just-shipped version?
- Or have all Android devices broken for some reason?
- Did you actually ship the bug 2 versions back but have only just realised now?

This is generally the hardest part of the process. Work to isolate and define the smallest subset of your user-base that
is affected.

### 4. Segment your Users based on the Bug

:::tip

We can make use of [Semver Aware Operators](/basic-features/managing-segments#semver-aware-operators) to drive these
Segment rules.

:::

From your work in #3, create a [Segment](/basic-features/managing-segments.md) in Flagsmith that captures the defined
set of users from #3. Let's say we just shipped version `5.4.1`, but we have figured out that the bug actually showed up
in version `5.4.0`. Also, this issue is only affecting iOS devices; Android users don't have the problem. So our Segment
would contain 2 rules and read something like:

- Trait `platform` _equals_ `iOS`
- Trait `version` _semver >=_ `5.4.0` **AND** _semver<=_ `5.4.1`

### 5. Override your Feature with your Segment

Locate the feature that is causing the problem. Get to the Overrides tab, add the Segment you defined in #4, and set
that Feature Override to **_disabled_**.

And breathe...

## What just happened?

We've done the hard work and isolated which precise subset of users are affected by this issue. We want the feature to
continue to show and work for all our other users (in this case Android users and iOS users on versions older than
`5.4.0`), but we want to disable it for the affected users.

So we created a Segment that precisely identified the affected users, and then used that Segment to override the
feature, **_but just for those users_**.

## What happens next?

Firstly, (sounds obvious but who knows!) ship a fix! Push version 5.4.2 that fixes the issue. As users upgrade, their
`version` trait will automatically change to 5.4.2 and they will drop out of the Segment. Flagsmith will then start
sending an Enabled flag for this feature, and your users will have access to the feature that you just fixed.

We can keep this Segment and the override in place. In fact, it's really important that we do! Lots of people don't
bother upgrading their apps at all. That's fine though; with the Segment in place, they will never know that you shipped
a clanger.
