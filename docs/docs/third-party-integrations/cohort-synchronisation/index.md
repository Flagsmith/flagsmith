---
title: Cohort Synchronisation
description: Synchronise cohorts from a CSV file or your analytics platform into Flagsmith as segments
sidebar_label: Overview
sidebar_position: 1
---

# Cohort Synchronisation

Cohort synchronisation lets you target feature flags at a group of users that you have defined outside Flagsmith. You
can upload a list of identifiers as a CSV file, or connect an analytics platform and synchronise a cohort you have
already built there. Either way, the group arrives in Flagsmith as a segment that you can use to override features.

This is useful when membership of the group depends on data Flagsmith does not hold. You can roll out to the power users
your analytics platform has identified, run a beta with a list of customers from your CRM, or turn a feature off for the
accounts named in a support ticket.

:::info

Cohort synchronisation is available on paid plans.

:::

:::warning Synchronised segments belong to one environment

You choose the environment when you set the segment up, and it cannot be changed afterwards. The segment has no members
in any other environment, so an override you add in, say, Production will not match anyone if the segment was
synchronised into Development. To target the same group in another environment, set the segment up again there.

:::

## Supported sources

- [CSV import](/third-party-integrations/cohort-synchronisation/csv-import)
- [Amplitude](/third-party-integrations/cohort-synchronisation/amplitude)

## Creating a synchronised segment

Every source starts in the same place. Go to the **Segments** page in your project, click **Create Segment**, and choose
how you want to define the segment.

![Create Segment source options](/img/cohort-synchronisation/create-segment-sources.png)

Choosing anything other than **Manually** creates a synchronised segment, and the steps that follow depend on the source
you picked.

## How it works

- **Each cohort becomes a segment.** Flagsmith creates the segment when you upload your first CSV file, or when your
  analytics platform sends the cohort for the first time. The segment appears on your Segments page alongside your other
  segments and can be used in segment overrides in the same way.
- **The source owns the membership.** You cannot edit the segment's rules in Flagsmith. To change who belongs to it,
  upload a new CSV file or change the cohort definition in your analytics platform.
- **Members are matched by identity identifier.** Each entry is matched to the Flagsmith
  [identity](/flagsmith-concepts/identities) with the same identifier, so your application must identify users with the
  same value that the source sends.
- **Synchronisation is scoped to one environment.** You choose the environment when you set the segment up, and members
  are synchronised into that environment only. The segment will not match anyone in your other environments.
- **Updates arrive differently per source.** A connected analytics platform sends membership changes on its own
  schedule, so its segments stay up to date on their own. A CSV segment changes only when you upload a new file.
- **Changes are applied in the background.** A large membership can take a few minutes to be reflected in full.

## Synchronisation keys

Analytics platforms authenticate with Flagsmith using a **cohort synchronisation key**. CSV uploads do not need one,
because you are already signed in to the dashboard.

- Keys are created per environment and work for any supported analytics platform.
- The key value is shown only once, at creation. Store it securely. If you lose it, create a new key.
- You can create several keys per environment, and revoke any of them at any time from **Environment Settings >
  Cohorts**. Revoking a key immediately stops the synchronisation that uses it.
- Creating and revoking keys requires the _Manage segment overrides_ permission for the environment and the _Manage
  segments_ permission for the project.

![Environment Settings Cohorts tab](/img/cohort-synchronisation/environment-settings-cohorts.png)

## Using a synchronised segment

Once the first synchronisation completes, the segment appears on the **Segments** page of your project, labelled with
the source it came from.

![Segments page with a synchronised segment](/img/cohort-synchronisation/synchronised-segment-list.png)

From there it behaves like any other segment. Click on a feature in the connected environment, go to the **Segment
Overrides** tab, and create an override for it. Identities that belong to the segment, and that your application
identifies with the same identifier, will receive the overridden flags.

Keep in mind:

- The segment only has members in the environment you chose when you set it up.
- Membership reflects the last synchronisation, not the current state of your data.

## Deleting a synchronised segment

Delete the segment from the **Segments** page like any other segment. Flagsmith removes its membership data as part of
the deletion.

If the segment was fed by an analytics platform, stop the cohort synchronisation there as well. If the platform keeps
sending updates for a segment that no longer exists, Flagsmith rejects them, and the platform will report the
synchronisation as failing and may pause it.

## Revoking access

To stop all synchronisation from analytics platforms into an environment, revoke its synchronisation keys in
**Environment Settings > Cohorts**. Existing segments and their members stay in place, but no further membership updates
are accepted for a revoked key.
