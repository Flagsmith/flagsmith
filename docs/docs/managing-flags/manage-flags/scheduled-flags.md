---
title: Scheduled Flags
sidebar_label: Scheduled Flags
sidebar_position: 3
---

Scheduled flags allow you to queue and automatically apply changes to feature flags at a specified future time, eliminating the need for manual intervention at the exact moment of change. This page shows you how to schedule flag changes.

There are two methods for creating a scheduled feature flag change:

- As part of a change request.
- Directly while editing a feature flag, if change requests are not enforced.

## Prerequisites

- To schedule feature flag changes with a change request, you must [have change requests enabled](/administration-and-security/governance-and-compliance/change-requests) in your environment. This is not necessary to directly schedule changes when editing a flag.
- Scheduled flags are available only for our **Scale-up** and **Enterprise** plans.

---

## How to create a Scheduled Flag change as part of a Change Request

1. Ensure your environment has change requests enabled.
2. Attempt to change a feature flag value within the environment. You will be prompted to create a new change request.
3. Fill in the following details:
   - The title of the change request
   - (Optional) A description of the reason for the change request
   - The date and time at which you want the feature flag change to take effect
4. Submit the change request. The scheduled change will appear in the change request area as 'Pending'.

---

## How to create a stand-alone scheduled feature flag change

If change requests are not enabled for your environment, you can schedule a flag change directly:

1. In the Features list view, go to the feature flag you want to edit.
2. Choose the new value or state for the feature flag.
3. Click the **Schedule Update** button to set the date and time for the change to take effect.
4. Save your changes. The scheduled change will be queued and applied automatically at the specified time.

---

## Scheduled Flags and Change Requests

Scheduled feature flags awaiting application will be listed in the change request area as 'Pending'.

Once the scheduled date and time have passed and the feature flag change has been applied, the scheduled feature flag will automatically move to the 'Closed' list in the change request area.

---

## What's next?

- To learn more about managing and approving changes to your feature flags, see the [change requests](/administration-and-security/governance-and-compliance/change-requests) page.
- To learn how to monitor the performance and health of your feature flags, see the [feature health metrics](./feature-health-metrics.md) page.
