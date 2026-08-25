---
title: SCIM provisioning
sidebar_label: SCIM
sidebar_position: 15
---

:::info

SCIM provisioning requires an [Enterprise subscription](https://flagsmith.com/pricing).

:::

SCIM (System for Cross-domain Identity Management) is a standard protocol for automating user and group provisioning
between your identity provider and Flagsmith. It lets your identity provider push changes to Flagsmith automatically, so
you do not need to manage users manually or wait for them to log in.

With SCIM, you can:

- Create Flagsmith users ahead of their first login, so they already have the right group memberships and permissions
  waiting for them.
- Deactivate or remove users from your Flagsmith organisation when they are deprovisioned in your identity provider.
- Sync group membership so that adding or removing a user from a group in your identity provider is reflected in
  Flagsmith automatically.

SCIM works alongside your existing SSO configuration: SSO handles authentication (how users log in), while SCIM handles
provisioning (which users and groups exist in Flagsmith, and who belongs to what).

## Supported features

Flagsmith's SCIM 2.0 API supports:

- Creating users.
- Deactivating and reactivating users through the `active` attribute. See [Deactivating users](#deactivating-users).
- Deleting users. See [User lifecycle](#user-lifecycle) for what is and is not removed.
- Pushing groups: create and update [permission groups](/administration-and-security/access-control/rbac#groups) and
  their membership, and delete groups.
- Filtering and pagination on the `/Users` and `/Groups` list endpoints.

Flagsmith does not support:

- Profile sourcing, `/Me`, `/Bulk`, sorting, and ETag concurrency control.

## Prerequisites

- Your Flagsmith organisation must have an active Enterprise licence.
- You must have an SSO configuration (such as [SAML](/administration-and-security/access-control/saml)) set up for your
  organisation. SCIM manages the user and group lifecycle, but users still authenticate through your SSO provider.

## User lifecycle

:::caution

Flagsmith requires the SCIM `userName` attribute to be the user's email address. Ensure your identity provider is
configured to send email addresses as SCIM usernames.

:::

When your identity provider provisions a user through SCIM:

1. If the user does not exist in Flagsmith, they are created with the email, first name and last name from the SCIM
   request. They are added to the organisation as a regular user.
2. If the user already exists (matched by email, case-insensitive), they are added to the organisation if they are not
   already a member.

When your identity provider deprovisions a user by sending a DELETE request:

1. The user is removed from the organisation in Flagsmith. This also removes all their project and environment
   permissions within that organisation, and removes them from all
   [permission groups](/administration-and-security/access-control/rbac#groups) in that organisation.
2. The user's data (audit log entries, change request history) is preserved.

### Deactivating users

Deactivation is the reversible alternative to deletion. Setting the SCIM `active` attribute to `false` — through either
a PUT or a PATCH request — deactivates the user's membership of the organisation:

1. The user can still log in to Flagsmith, but cannot access the organisation, and no longer sees it in their
   organisation picker.
2. The membership no longer counts towards your plan's seat limit.
3. Their role, project and environment permissions, and
   [permission group](/administration-and-security/access-control/rbac#groups) memberships are all retained.

Setting `active` back to `true` reactivates the membership and restores access exactly as it was. A reactivated member
takes up a seat again. Reactivation always succeeds, even when that takes you over your plan's seat limit — your
identity provider stays the source of truth, and the extra seats are billed as an overage.

Deactivated members remain visible over SCIM: a GET on the user returns `200` with `"active": false`, and they appear in
`/Users` list responses.

:::tip

Prefer deactivation over deletion when a user might return, or when you want to preserve their permissions while they
are on leave. Use DELETE when you want the membership and its permissions gone for good.

:::

### User attributes

Flagsmith reads the following attributes from SCIM user requests:

| Attribute         | Required | Maps to                        |
| ----------------- | -------- | ------------------------------ |
| `userName`        | Yes      | Email address                  |
| `name.givenName`  | No       | First name                     |
| `name.familyName` | No       | Last name                      |
| `active`          | No       | Organisation membership status |

All other attributes are ignored. If your identity provider lets you choose which attributes to send, sending only the
four above keeps your configuration simpler and avoids implying that Flagsmith stores data it does not.

## Group lifecycle

SCIM groups map to Flagsmith [permission groups](/administration-and-security/access-control/rbac#groups) within the
organisation. Groups are matched by the `externalId` field in the SCIM request, which corresponds to the "External ID"
field on Flagsmith permission groups — the same field used by
[SAML group sync](/administration-and-security/access-control/saml#using-groups-from-your-saml-idp).

When your identity provider creates or updates a group through SCIM:

1. If no Flagsmith permission group with a matching external ID exists in the organisation, one is created with the
   display name and external ID from the SCIM request.
2. Group membership is synced to match the SCIM request: users are added or removed as needed.

When your identity provider deletes a group through SCIM:

1. All users are removed from the group.
2. The group is deleted from the organisation.

### Interaction with SAML group sync

If you have [SAML group sync](/administration-and-security/access-control/saml#using-groups-from-your-saml-idp)
configured, both SCIM and SAML will manage group membership. SCIM changes are applied as they arrive from your identity
provider. SAML group sync is applied at login time. The two mechanisms are complementary: SCIM keeps groups current
between logins, while SAML group sync acts as a reconciliation point at each login.

## Setup

### 1. Create a SCIM configuration

From the Flagsmith dashboard, go to **Organisation Settings** > **SSO** > **SCIM**.

Click "Create SCIM Configuration". This generates a SCIM bearer token. Copy this token and store it securely. It is
shown only once and cannot be retrieved later. If you lose it, you can regenerate a new token from the same page.

### 2. Configure your identity provider

Add Flagsmith as a SCIM application in your identity provider. You will need:

- **SCIM base URL**: `https://flagsmith.example.com/api/v1/scim/v2`, replacing `flagsmith.example.com` with your
  Flagsmith API domain. On Flagsmith SaaS, this is `https://api.flagsmith.com/api/v1/scim/v2`.
- **Bearer token**: the token you copied in the previous step.

Both values are shown on the SCIM page in Flagsmith, so you can copy them directly rather than assembling the URL by
hand.

The exact steps depend on your identity provider. See the guides below for common providers.

### 3. Assign users and groups

In your identity provider, assign users and groups to the Flagsmith SCIM application. Your identity provider will begin
pushing these to Flagsmith immediately.

## Managing SCIM tokens

You can view and manage SCIM configurations from **Organisation Settings** > **SSO** > **SCIM**. From this page you can:

- Regenerate a SCIM token. This invalidates the previous token immediately.
- Delete the SCIM configuration. This stops all SCIM provisioning for the organisation. Existing users and groups are
  not removed.

## Identity provider guides

:::note

These guides were last verified in July 2026. If your identity provider's UI has changed, refer to their documentation
for the most up-to-date steps.

:::

### Okta

These steps are for the Flagsmith application from the Okta Integration Network catalogue.

1. Get your SCIM bearer token as described under [Setup](#1-create-a-scim-configuration).
1. Go to the "Applications" page and open the Flagsmith application.
1. On the "Sign On" tab, under "Advanced Sign-on Settings", set API Base URL to your Flagsmith API domain. On Flagsmith
   SaaS this is `https://api.flagsmith.com`.
1. Still on the "Sign On" tab, under "Credentials Details", set the application username format to "Email". Flagsmith
   requires the SCIM `userName` to be a valid email address.
1. Go to the "General" tab, click "Edit" under "App Settings", enable "Provisioning" and click "Save". A "Provisioning"
   tab appears.
1. On the "Provisioning" tab, select "Integration" and click "Edit". Tick "Enable API integration" and paste your SCIM
   bearer token into **API Token**.
1. Click "Test API Credentials" to verify the connection, then save.
1. Select "To App" and click "Edit", then enable "Create Users", "Update User Attributes" and "Deactivate Users".

To deactivate a user, deactivate them in Okta or unassign them from the application. Okta sends `active: false` and
Flagsmith deactivates their membership, freeing their seat while preserving their permissions. Reactivating them in Okta
restores their access.

To remove a user entirely, delete them from Okta. Okta sends a DELETE request and Flagsmith removes the user from your
organisation along with their permissions.

To sync groups, use the "Push Groups" tab to select the Okta groups you want to push to Flagsmith.

### Microsoft Entra ID (Azure AD)

1. In the Entra admin centre, go to Enterprise Applications and find your Flagsmith application.
2. Go to "Provisioning" and click "Get started".
3. Set the provisioning mode to "Automatic".
4. Under "Admin Credentials", set the tenant URL to your Flagsmith SCIM base URL and the secret token to your SCIM
   bearer token.
5. Click "Test Connection" to verify, then save.
6. Under "Mappings", configure the user and group attribute mappings. Ensure `emails[type eq "work"].value` maps to the
   user's email address.
7. Set the provisioning status to "On" and save.

### OneLogin

1. In the OneLogin admin panel, go to Applications and find your Flagsmith application.
2. Go to "Configuration" and set the SCIM base URL and SCIM bearer token.
3. Go to "Provisioning" and enable provisioning.
4. Under "Entitlements", configure which users and groups should be pushed to Flagsmith.

## SCIM API

Flagsmith implements a SCIM 2.0 API (RFC 7643, RFC 7644) with endpoints for managing users, groups, and discovering
service provider capabilities. The full API specification is available in the
[Swagger documentation](https://api.flagsmith.com/api/v1/docs/).

All SCIM endpoints are under `/api/v1/scim/v2/` and require a valid SCIM bearer token in the `Authorization` header. The
API supports filtering (e.g. `filter=userName eq "user@example.com"`) and pagination (`startIndex`, `count`) on list
endpoints as defined by the SCIM 2.0 specification.

## Troubleshooting

### Users are not being provisioned

- Verify the SCIM base URL in your identity provider matches the one shown in Flagsmith under **Organisation
  Settings** > **SSO** > **SCIM**.
- Verify the bearer token is correct. If in doubt, regenerate it.
- Check that the SCIM `userName` attribute is the user's email address. Flagsmith rejects requests with a non-email
  `userName` with a 400 response.

### Users are provisioned but cannot log in

- SCIM only manages the user lifecycle (creating accounts, setting group membership). Users still need to authenticate
  through your SSO provider. Verify that your SAML configuration is set up correctly.

### Group membership is not syncing

- Verify that the `externalId` in the SCIM group request matches the "External ID" on the corresponding Flagsmith
  permission group. If the group was created by SCIM, this is set automatically.
- If you are also using SAML group sync, note that SAML will re-sync group membership at each login. The two mechanisms
  are designed to work together, but if they use different group identifiers, they may conflict.

### Deprovisioned users still appear in the organisation

- Deactivated users are intentionally retained. They keep their `active: false` membership so they can be reactivated
  later, and they do not count towards your seat limit. If you want the membership gone entirely, your identity provider
  must send a DELETE request.
- Check that your identity provider is configured to send deprovisioning events at all — in Okta, for example,
  "Deactivate Users" must be enabled under "Provisioning to App".

### Reactivated users took the organisation over its seat limit

- Reactivating a deactivated member takes up a seat again, and Flagsmith does not block reactivation to keep you within
  your plan's limit — doing so would leave your identity provider and Flagsmith out of sync. The additional seats are
  billed as an overage. Deactivate or remove members in your identity provider to bring the count back down.
