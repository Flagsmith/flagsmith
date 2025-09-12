# Change Requests

:::tip

Change requests are part of our Scale-Up and Enterprise plans.

:::

## Overview

You can use Change Requests to add workflow control to the changing of Flag values. Change Requests allow a user to
propose a change to a flag value, and then require that change is approved by a number of other team members.

You can use Change Requests to ensure that, for example, a change to a flag in Production has to be approved by another
team member. They work in a similar way to Pull Requests in git.

## Setting up Change Requests

Change Requests are configured at the Environment level. To enable Change Requests, go to the Environment Settings Page,
Enable the Change Request setting, and select how many approvals you would like for each Change Request to be applied.

## Creating a Change Request

:::info

Any user that has permission to _Update_ a Feature within the Environment can create a Change Request

:::

Once an Environment is configured with Change Requests enabled, attempting to change a flag value will prompt you to
create a new Change Request.

You will need to provide:

- The title of the Change Request
- Optionally a description of the reason for the Change Request
- Assigness - specify either individual users or members of a group. These users will receive an email alerting them of the Change Request

## Approving a Change Request

:::info

Any user that has permission to write to the Environment containing the Change Request can approve it.

:::

Change Requests awaiting approval are listed in the Change Request area.

Clicking on a Change Request brings up the details of the request, and the current and new Flag values.

## Publishing a Change Request

When the required number of approvals have been made, you will be able to publish the Change Request.

The Change Request will immediately come into effect once the Publish Change button is clicked.
