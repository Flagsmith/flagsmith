---
title: Flag Analytics
---

## Overview

Flag Analytics allow you to track how often individual Flags are evaluated within the Flagsmith SDK.

To view Analytics for a particular flag, browse to the relevant environment and click on a single flag to edit that
flag.

![Image](/img/flag-analytics.png)

Flag Analytics can be really useful when removing flags from Flagsmith. More often than not, flags can be removed from
your codebase and platform once they have been rolled out and everyone is comfortable with them running in production.

Once you have removed the evaluation code from your code base, its nice to be sure that all references to that flag have
been removed, and that removing the flag itself from Flagsmith will not cause any unforeseen issues. Flag Analytics help
with this.

Flag Analytics can also be helpful when identifying integration issues. Occasionally errors can creep into your code
that cause multiple needless evaluations of a flag. Again, these analytics can help isolate these situations.

## Enabling Flag Analytics?

:::info

The Flag Analytics data will be visible in the Dashboard between 30 minutes and 1 hour after it has been collected.

:::

Flag analytics are disabled by default in our SDKs. You need to explicitly enable it when you initialize the Flagsmith
client. Please refer to the corresponding SDK documentation for more details. For the Javascript family SDKs please
refer to [Initialisation options](https://docs.flagsmith.com/clients/javascript#initialisation-options).

## How does it work?

Every time a flag is evaluated within the SDK (generally a call to a method like
`flagsmith.hasFeature("myCoolFeature")`), the SDK keeps a track of the flag name along with an evaluation count.

Every `n` seconds (currently set to 10 seconds in the JS SDK) the SDK sends a message to the Flagsmith API with the list
of flags that have been evaluated and their count. If no flags have been evaluated in that time window, no message is
sent.
