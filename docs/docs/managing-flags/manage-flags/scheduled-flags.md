---
title: Scheduled Flags
sidebar_label: Scheduled Flags
sidebar_position: 3
---

Scheduled Flags allow you to queue and automatically apply changes to feature flags at a specified future time, eliminating the need for manual intervention at the exact moment of change. This page shows you how to schedule flag changes.

There are two methods for creating a Scheduled Flag change:

- As part of a Change Request.
- Directly while editing a feature flag, if Change Requests are not enforced.

## Prerequisites

- To schedule flag changes with a Change Request, you must [have Change Requests enabled](../../advanced-use/change-requests.md) in your environment. This is not necessary to directly schedule changes when editing a flag.
- Scheduled Flags are available only for our **Scale-up** and **Enterprise** plans.

---

## How to create a Scheduled Flag change as part of a Change Request

1. Ensure your Environment has Change Requests enabled.
2. Attempt to change a flag value within the environment. You will be prompted to create a new Change Request.
3. Fill in the following details:
   - The title of the Change Request
   - (Optional) A description of the reason for the Change Request
   - The date and time at which you want the flag change to take effect
4. Submit the Change Request. The scheduled change will appear in the Change Request area as 'Pending'.

---

## How to create a stand-alone Scheduled Flag change

If Change Requests are not enabled for your environment, you can schedule a flag change directly:

1. In the Features list view, go to the feature flag you want to edit.
2. Choose the new value or state for the flag.
3. Click the **Schedule Update** button to set the date and time for the change to take effect.
4. Save your changes. The scheduled change will be queued and applied automatically at the specified time.

---

## Scheduled Flags and Change Requests

Scheduled Flags awaiting application will be listed in the Change Request area as 'Pending'.

Once the scheduled date and time have passed and the flag change has been applied, the Scheduled Flag will automatically move to the 'Closed' list in the Change Request area.

---

## What's next?

- To learn more about managing and approving changes to your flags, see the [Change Requests](../../advanced-use/change-requests.md) page.
- To learn how to monitor the performance and health of your feature flags, see the [Feature Health Metrics](../feature-health-metrics.md) page.
