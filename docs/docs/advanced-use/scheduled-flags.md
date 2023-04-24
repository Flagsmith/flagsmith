# Scheduled Flags

:::tip

Scheduled Flags are part of our Scale-Up and Enterprise plans.

:::

## Overview

You can use Scheduled Flags to queue up changes to Flags to be modified automatically in a future point in time.

You can create a Scheduled Flag change in 1 of two ways:

- As part of a Change Request.
- If you are not enforcing Change Requests, you can schedule the Flag change when modifying a Flag.

## Creating a Scheduled Flag change as part of a Change Request

Once an Environment is configured with Change Requests enabled, attempting to change a flag value will prompt you to
create a new Change Request.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/change-request-schedule.png"/></div>

You will need to provide:

- The title of the Change Request
- Optionally a description of the reason for the Change Request
- The Date and Time that you want the flag change to take effect

## Creating a stand-alone Scheduled Flag change

If the Environment you are working with does not have Change Requests enabled, you can create a Scheduled Flag Change
directly from when editing the Flag.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/scheduled-flag-create.png"/></div>

## Scheduled Flags and Change Requests

Scheduled Flags pending go live will appear in the Change Request area.

![Listing Scheduled Flags](/img/scheduled-flag-list.png)

Once the Schedule of the flag has passed the Scheduled Flag will move to the "Closed" list.
