---
title: System Administration
---

## Authentication

Flagsmith supports a variety of Authentication methods for logging into the dashboard.

### Open Source Version

- Username and Password
- Github OAuth (with configuration)
- Google OAuth (with configuration)

### SaaS, Free and Startup Plans

- Username and Password
- Github OAuth (with configuration)
- Google OAuth (with configuration)

### SaaS, Scale-Up Plan

2FA can also be enabled with this plan.

- Username and Password
- Github OAuth (with configuration)
- Google OAuth (with configuration)
- SAML

### Enterprise Plan (SaaS, On Prem or Private Cloud)

2FA can also be enabled with this plan.

Enterprise plans also allows for restrictions to lock down Organisation logins to specific authentication methods.

- Username and Password
- Github OAuth (with configuration)
- Google OAuth (with configuration)
- SAML
- Okta
- LDAP
- Microsoft ADFS

## Terraform API Keys for Organisations

You can create Terraform API Keys from the Organisation Settings page. These are currently used with our
[Terraform Provider](../integrations/terraform.md). You can create Terraform API Keys that have access over your entire
Organisation for the endpoints required by Terraform to operate.

## Preventing Client SDKS from setting Traits

There may be use-cases where you want to prevent client-side SDKs from setting traits of users. For example, if you are
setting `plan=silver` as a trait, and then enabling/disabling features based on that plan, a malicious user could, with
a client-side SDK, update their trait to `plan=gold` and unlock features they have not paid for.

You can prevent this by disabling the "Allow client SDKs to set user traits" option. This option defaults to "On".
Turning it "Off" will not allow client-side SDKs to write Traits to Flagsmith. In order to write traits, you will need
to use a [server-side SDK and server-side Key](../clients/overview.md).

This is a per-Environment setting.

## API Usage

Flagsmith will track API calls made by the SDKS and store them in its data-store. You can view this data by going to the
Organisation settings page and clicking on **Usage**. You can also drill down into Projects and Environments. Flagsmith
tracks the following request types:

1. Get Flags
2. Get Identity Flags
3. Set Identity Traits
4. Get Environment Document (for local evaluation SDKs)

![API Usage](/img/api-usage.png)

## Audit Logs

Every action taken within the Flagsmith administration application is tracked and logged. This allows you to easily
retrace the events and values that flags, identities and segments have taken over time.

You can view the Audit Log within the Flagsmith application, and filter it in order to find the information you are
after.

You can also stream your Audit Logs into your own infrastructure using [Audit Log Webhooks](#audit-log-webhooks).

## Audit Log Webhooks

You can use Audit Log Webhooks to stream your Organisation's Audit Log into your own infrastructure. This can be useful
for compliance or to reference against local CI/CD infrastructure.

```json
{
 "created_date": "2020-02-23T17:30:57.006318Z",
 "log": "New Flag / Remote Config created: my_feature",
 "author": {
  "id": 3,
  "email": "user@domain.com",
  "first_name": "Kyle",
  "last_name": "Johnson"
 },
 "environment": null,
 "project": {
  "id": 6,
  "name": "Project name",
  "organisation": 1
 },
 "related_object_id": 6,
 "related_object_type": "FEATURE"
}
```

## Web Hooks

You can use the Web Hooks to send events from Flagsmith into your own infrastructure. Web Hooks are managed at an
Environment level, and can be configured in the Environment settings page.

![Image](/img/add-webhook.png)

Currently the following events will generate a Web Hook action:

- Creating Features (Sent as event_type `FLAG_UPDATED`)
- Updating Feature value / state in an Environment (Sent as event_type `FLAG_UPDATED`)
- Overriding a Feature for an Identity (Sent as event_type `FLAG_UPDATED`)
- Overriding a Feature for a Segment (Sent as event_type `FLAG_UPDATED`)

You can define any number of Web Hook endpoints per Environment. Web Hooks can be managed from the Environment settings
page.

A typical use case for Web Hooks is if you want to cache flag state locally within your server environment.

Each event generates an HTTP POST with the following body payload to each of the Web Hooks defined within that
Environment:

```json
{
 "data": {
  "changed_by": "Ben Rometsch",
  "new_state": {
   "enabled": true,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show html in a butter bar for certain users",
    "id": 7168,
    "initial_value": null,
    "name": "butter_bar",
    "project": {
     "id": 12,
     "name": "Flagsmith Website"
    },
    "type": "CONFIG"
   },
   "feature_segment": null,
   "feature_state_value": "<strong>\nYou are using the develop environment.\n</strong>",
   "identity": null,
   "identity_identifier": null
  },
  "previous_state": {
   "enabled": false,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show html in a butter bar for certain users",
    "id": 7168,
    "initial_value": null,
    "name": "butter_bar",
    "project": {
     "id": 12,
     "name": "Flagsmith Website"
    },
    "type": "CONFIG"
   },
   "feature_segment": null,
   "feature_state_value": "<strong>\nYou are using the develop environment.\n</strong>",
   "identity": null,
   "identity_identifier": null
  },
  "timestamp": "2021-06-18T07:50:26.595298Z"
 },
 "event_type": "FLAG_UPDATED"
}
```

## Webhook Signature

When your webhook secret is set, Flagsmith uses it to create a hash signature with each payload. This hash signature is
passed with each request under the X-Flagsmith-Signature header that you need to validate at your end

### Validating Signature

Compute an HMAC with the SHA256 hash function. Use request body (raw utf-8 encoded string) as the message and secret
(utf8 encoded) as the Key. Here is one example in Python:

```python
import hmac

secret = "my shared secret"

expected_signature = hmac.new(
    key=secret.encode(),
    msg=request_body,
    digestmod=hashlib.sha256,
).hexdigest()

received_signature = request["headers"]["x-flagsmith-signature"]
hmac.compare_digest(expected_signature, received_signature) is True
```

## Environment Banners

You can optionally provide a coloured banner for your Environments in each Environment Settings page. This helps you
identify sensitive Environments before toggling flags!

![Environment Banners](/img/environment-banner.png)

## Hide Sensitive Data

Enabling this feature within the environment will return null for sensitive or unused fields in the response generated
by the SDK endpoints.

### `/api/v1/flags`

The following fields will always be Null:

- `id`
- `feature.created_date`
- `feature.description`
- `feature.initial_value`
- `feature.default_enabled`
- `feature_segment`
- `environment`
- `identity`

The response from `/api/v1/flags` will change from this:

```json
[
 {
  "id": 27595,
  "feature": {
   "id": 9422,
   "name": "first_feature",
   "created_date": "2023-05-14T06:11:08.178802Z",
   "description": null,
   "initial_value": null,
   "default_enabled": false,
   "type": "STANDARD"
  },
  "feature_state_value": null,
  "environment": 5242,
  "identity": null,
  "feature_segment": null,
  "enabled": false
 },
 {
  "id": 27597,
  "feature": {
   "id": 9423,
   "name": "second_feature",
   "created_date": "2023-05-14T06:29:29.542708Z",
   "description": null,
   "initial_value": null,
   "default_enabled": false,
   "type": "STANDARD"
  },
  "feature_state_value": null,
  "environment": 5242,
  "identity": null,
  "feature_segment": null,
  "enabled": false
 }
]
```

To this:

```json
[
 {
  "id": null,
  "feature": {
   "id": 9422,
   "name": "first_feature",
   "created_date": null,
   "description": null,
   "initial_value": null,
   "default_enabled": null,
   "type": "STANDARD"
  },
  "feature_state_value": null,
  "environment": null,
  "identity": null,
  "feature_segment": null,
  "enabled": false
 },
 {
  "id": null,
  "feature": {
   "id": 9423,
   "name": "second_feature",
   "created_date": null,
   "description": null,
   "initial_value": null,
   "default_enabled": null,
   "type": "STANDARD"
  },
  "feature_state_value": null,
  "environment": null,
  "identity": null,
  "feature_segment": null,
  "enabled": false
 }
]
```

:::info

All fields mentioned are not part of the response generated by the [Edge API](./edge-api.md).

:::

### `/api/v1/identities`

The following fields will always be Null:

- `flags[].id`
- `flags[].feature.created_date`
- `flags[].feature.description`
- `flags[].feature.initial_value`
- `flags[].feature.default_enabled`
- `flags[].feature_segment`
- `flags[].environment`
- `flags[].identity`
- `traits[]`

The response for `/api/v1/identities` will change from this:

```json
{
 "traits": [{ "id": 1, "trait_key": "key", "trait_value": "value" }],
 "flags": [
  {
   "id": 27595,
   "feature": {
    "id": 9422,
    "name": "first_feature",
    "created_date": "2023-05-14T06:11:08.178802Z",
    "description": null,
    "initial_value": null,
    "default_enabled": false,
    "type": "STANDARD"
   },
   "feature_state_value": null,
   "environment": 5242,
   "identity": null,
   "feature_segment": null,
   "enabled": false
  },
  {
   "id": 27597,
   "feature": {
    "id": 9423,
    "name": "second_feature",
    "created_date": "2023-05-14T06:29:29.542708Z",
    "description": null,
    "initial_value": null,
    "default_enabled": false,
    "type": "STANDARD"
   },
   "feature_state_value": null,
   "environment": 5242,
   "identity": null,
   "feature_segment": null,
   "enabled": false
  }
 ]
}
```

To this

```json
{
 "traits": [],
 "flags": [
  {
   "id": null,
   "feature": {
    "id": 9422,
    "name": "first_feature",
    "created_date": null,
    "description": null,
    "initial_value": null,
    "default_enabled": null,
    "type": "STANDARD"
   },
   "feature_state_value": null,
   "environment": null,
   "identity": null,
   "feature_segment": null,
   "enabled": false
  },
  {
   "id": null,
   "feature": {
    "id": 9423,
    "name": "second_feature",
    "created_date": null,
    "description": null,
    "initial_value": null,
    "default_enabled": false,
    "type": "STANDARD"
   },
   "feature_state_value": null,
   "environment": null,
   "identity": null,
   "feature_segment": null,
   "enabled": false
  }
 ]
}
```

:::info

Responses generated by [Edge API](./edge-api.md) already excludes all the above mentioned fields apart from `traits`

:::
