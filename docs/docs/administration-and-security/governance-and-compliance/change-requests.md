---
title: Change Requests
sidebar_label: Change Requests
sidebar_position: 10
---

You can use Change Requests to add workflow control to the changing of Flag values. Change Requests allow a user to propose a change to a flag value, and then require that change is approved by a number of other team members.

You can use Change Requests to ensure that, for example, a change to a flag in Production has to be approved by another team member. They work in a similar way to Pull Requests in git. This guide explains how to use Change Requests to add workflow control to changing flag values. You will learn how to set up, create, approve, and publish Change Requests. 

## Prerequisites

- Change Requests are available only with our Scale-Up and Enterprise plans. Make sure you are subscribed to one of these.

## Set Up Change Requests

Change Requests are configured at the environment level. To enable and set up Change Requests:

1.  Go to the **Environment Settings Page**.
2.  Enable the **Change Request** setting.
3.  Select the required number of approvals for each Change Request to be applied.

## Create a Change Request

Once an environment is configured with Change Requests enabled, attempting to change a flag value will prompt you to create a new Change Request.

:::info

Any user with permission to *update* a feature within the environment can create a Change Request.

:::

When creating a Change Request, you will need to provide the following:

* The **title** of the Change Request.
* An **optional description** of the reason for the Change Request.
* Any number of **assignees**. These individuals will receive an email notification about the Change Request.

## Approve a Change Request

Change Requests awaiting approval are listed in the **Change Request** area.

:::info

Any user with permission to write to the environment containing the Change Request can approve it.

:::

1.  Click on a **Change Request** to view its details.
2.  Review the current and new Flag values.

## Publish a Change Request

When the required number of approvals have been made, you will be able to publish the Change Request.

The Change Request will immediately come into effect once the **Publish Change** button is clicked.
