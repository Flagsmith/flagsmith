---
title: Amplitude Cohort Synchronisation
description: Synchronise Amplitude cohorts into Flagsmith as segments
sidebar_label: Amplitude
sidebar_position: 3
---

# Amplitude

Flagsmith is available as a cohort destination in Amplitude's catalogue. Once connected, every Amplitude cohort you
synchronise appears in Flagsmith as a segment, and Amplitude keeps its members up to date for you.

Read the [cohort synchronisation overview](/third-party-integrations/cohort-synchronisation) first for how synchronised
segments behave.

:::tip

Flagsmith matches cohort members to identities by identifier, so the Amplitude `user_id` must be the same value your
application uses as the Flagsmith [identity](/flagsmith-concepts/identities) identifier.

:::

## 1. Create a synchronisation key in Flagsmith

1. Go to the **Segments** page in your project and click **Create Segment**.
2. Choose **Amplitude**.
3. Select the environment you want to synchronise cohorts into.
4. Create a synchronisation key: give it a name, such as "Amplitude production", and copy the key value. It is shown
   only once. If the environment already has a key that you created earlier and still have, you can reuse it instead.

![Connect Amplitude modal](/img/cohort-synchronisation/connect-amplitude-modal.png)

## 2. Add Flagsmith as a destination in Amplitude

1. In Amplitude, go to **Data > Catalog > Destinations** and find **Flagsmith** in the cohort destinations catalogue.
2. Give the destination a recognisable name. Including the Flagsmith environment name is a good idea, because the key
   decides which environment the cohorts are synchronised into.
3. Paste your synchronisation key into the **Cohort sync api key** field.
4. Check the **Identifier Mapping**. Amplitude's **User ID** must map to the Flagsmith **Identifier**.

![Amplitude destination catalogue showing Flagsmith](/img/cohort-synchronisation/amplitude-destination-catalogue.png)

![Amplitude Flagsmith destination configuration](/img/cohort-synchronisation/amplitude-destination-config.png)

## 3. Synchronise a cohort

1. In Amplitude, open the cohort you want to target and click **Target users**.
2. Select your Flagsmith destination.
3. Choose the cadence, then click **Sync**:

   - **One-Time Sync** sends the cohort's current members once.
   - **Scheduled Sync** resends the membership every hour or every day.
   - **Real-Time Sync** resends the membership every minute.

   Scheduled and real time syncs keep the Flagsmith segment up to date on their own. With a one-time sync, later changes
   to the cohort do not reach Flagsmith until you synchronise it again.

![Amplitude Define Cadence dialog](/img/cohort-synchronisation/amplitude-define-cadence.png)

Shortly after the first synchronisation, a segment named after your cohort appears on the **Segments** page of your
project, ready to be used in
[segment overrides](/third-party-integrations/cohort-synchronisation#using-a-synchronised-segment).

## Notes

- Each cohort synchronisation you set up in Amplitude creates its own segment in Flagsmith. Synchronising the same
  cohort to a second destination creates a second segment.
- If you delete a synchronised segment in Flagsmith, stop the cohort synchronisation in Amplitude as well. Otherwise
  Amplitude reports the synchronisation as failing and may pause it.
