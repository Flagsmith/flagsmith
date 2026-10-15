---
title: Flag Dependencies
sidebar_label: Flag Dependencies
sidebar_position: 20
---

## Overview

Suppose you have a feature flag `coffee_machine`, but it needs another feature `hamster_power_grid` turned on so it can be evaluated as enabled. Flag dependencies allow for establishing prerequisites between flags.

![`coffee_machine` requires `hamster_power_grid`](/img/flag-dependencies/overview.png)

:::info Available in all plans

Flag dependencies are free and included in all plans.

:::

When the prerequisite feature is disabled, the dependent feature is also evaluated as _disabled_. By default, a feature prerequisite takes priority over segment overrides, but you can move overrides in the _Segment Overrides_ tab to adjust if necessary. As usual, identity overrides always take precedence.

![`coffee_machine` serving is off since `hamster_power_grid` is disabled](/img/flag-dependencies/serving-off.png)

## Adding a prerequisite to a feature flag

1. Go to the _Features_ list page.
2. Make sure you select the _environment_ on the left.
3. Select any feature in the list.
4. **Visit the _Dependencies_ tab**.
5. Click _Add prerequisite_, and choose from the list the prerequisite feature.

![Adding a prerequisite feature](/img/flag-dependencies/add-prerequisite.png)

For now, a prerequisite feature cannot have another prerequisite itself — dependencies only go one level deep. However, a feature can have as many prerequisites as necessary.

## Removing a prerequisite

Just click the 🗑️ icon next to the prerequisite feature you want to remove in the _Dependencies_ tab.

![Removing a prerequisite feature](/img/flag-dependencies/remove-prerequisite.png)

## Change requests

When _Feature change requests_ are enabled, changes to feature prerequisites will also require approval.

![Flag dependency changes wrapped in a change request](/img/flag-dependencies/requires-change-request.png)
