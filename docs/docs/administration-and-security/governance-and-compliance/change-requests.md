---
title: Change Requests
sidebar_label: Change Requests
sidebar_position: 10
---

You can use Change Requests to ensure that, for example, a change to a flag in Production has to be approved by another team member. They work in a similar way to Pull Requests in git. This guide explains how to use Change Requests to add workflow control to changing flag values. You will learn how to set up, create, approve, and publish Change Requests.

## Prerequisites

- Change Requests are available only with our Scale-Up and Enterprise plans. Make sure you are subscribed to one of these.

## Set Up Change Requests

Change Requests are configured at the environment level. To enable and set up Change Requests:

1.  Go to the **Environment Settings Page**.
2.  Enable the **Change Request** setting.
3.  Select the required number of approvals for each Change Request to be applied.

## Scope of Change Requests

Change Requests apply to **environment-level** and **segment-level** flag changes only. The workflow does not apply to identity-level overrides.

| Feature state type  | Scoped to                       | Requires a Change Request? |
| ------------------- | ------------------------------- | -------------------------- |
| Environment default | All users in an environment     | ✅ Yes                     |
| Segment override    | Users matching a segment        | ✅ Yes                     |
| Identity override   | A single specific identity      | ❌ No — live immediately   |

**Identity overrides are intentionally excluded.** They do not participate in
Flagsmith's versioning system, which is what the CR workflow is built on.
Changes to an identity override take effect the moment they are saved, with
no approval step.

:::tip
If your team requires approval gates on all flag changes, prefer
**segment-based targeting** (e.g. a `qa-team` segment) over individual
identity overrides. Segment overrides are subject to the full Change Request
workflow.
:::

## Create a Change Request

Once an environment is configured with Change Requests enabled, attempting to
change an environment default or segment override will prompt you to create a
new Change Request.

When creating a Change Request, you will need to provide the following:

* The **title** of the Change Request.
* An **optional description** of the reason for the Change Request.
* Any number of **assignees**. These individuals will receive an email
  notification about the Change Request.

## Approve a Change Request

Change Requests awaiting approval are listed in the **Change Request** area.

1.  Click on a **Change Request** to view its details.
2.  Review the current and new Flag values.
3.  Click **Approve** to record your decision.

## Publish a Change Request

When the required number of approvals have been made, you will be able to
publish the Change Request. The Change Request will immediately come into
effect once the **Publish Change** button is clicked.

## Notifications

Flagsmith sends email notifications at the following points in the Change
Request lifecycle:

| Event | Who is notified |
| ----- | --------------- |
| A Change Request is assigned to an individual | The assignee receives an email informing them that their approval is pending |
| A Change Request is approved | The CR author receives an email confirming the approval |
| A Change Request is assigned to a group | All members of the group receive a notification via background task |

:::note
**Self-hosting?** To ensure these email notifications are delivered correctly, you must configure the [self-hosted email setup](https://docs.flagsmith.com/deployment-self-hosting/core-configuration/email-setup).
:::

**What does not trigger a notification:**

- **Committing a Change Request** — no email is sent when a CR is published.
  Only audit log entries are created for the affected feature states.
- **Rejecting a Change Request** — there is no first-class rejection flow.
  Closing a CR means deleting it, and no email is sent on deletion.
- **Webhook events** — there are no webhook events for CR lifecycle changes.
  The organisation webhook receives audit log events only.

## Permissions

| Action                   | Required permission       |
| ------------------------ | ------------------------- |
| Create a Change Request  | Create change request     |
| Approve a Change Request | Approve change request    |
| Publish a Change Request | Update feature state      |

These permissions can be configured at both the project level and the
environment level. For example, you might allow all developers to create
change requests in Production, but only senior engineers to approve and
publish them. See
[Role-based access control](/administration-and-security/access-control/rbac)
for details on configuring permissions.
