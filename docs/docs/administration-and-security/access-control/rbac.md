---
title: Role-based access control
sidebar_label: Role-based Access Control
sidebar_position: 1
---

:::info

Role-based access control requires an [Enterprise subscription](https://www.flagsmith.com/pricing).

:::

Role-based access control (RBAC) provides fine-grained access management of Flagsmith resources. Using RBAC, you can
ensure users only have the access they need within your Flagsmith organisation.

For example, RBAC allows you to achieve the following scenarios:

- Only allow certain users to modify your production environments.
- Grant a default set of permissions to all users that join your Flagsmith organisation.
- Lock down an [Admin API](/integrating-with-flagsmith/flagsmith-api-overview/admin-api) key to a specific set of permissions.
- Provide Flagsmith permissions based on your enterprise identity provider's groups when using
  [SAML single sign-on](/administration-and-security/access-control/saml).

To add users to your Flagsmith organisation or to manage user permissions, click on your organisation name in the top
left and open the **Users and Permissions** tab.

## Core concepts

### How permissions are assigned

Permissions are granted to **[roles](#roles)**, and roles are assigned to users, [groups](#groups), or [Admin API keys](/integrating-with-flagsmith/flagsmith-api-overview/admin-api/authentication). A user's effective permissions are the **union of all permissions** from every role assigned to them — both directly and through group membership.

![How permissions are assigned](/img/rbac-permissions-diagram.svg)

### Permission levels

Permissions in Flagsmith are managed at three levels that align with the data hierarchy. Understanding which permissions apply at which level is critical for setting up access control correctly.

![Permission hierarchy: Organisation → Project → Environment](/img/permission-hierarchy.svg)

### Roles

A role is a set of permissions that, when assigned, allows performing specific actions on your organisation, projects or
project environments.

#### Organisation-level roles

Every user in your organisation has exactly one of these built-in organisation roles:

- _Organisation Administrator_ — full access to everything in your Flagsmith organisation
- _User_ — no default access; requires permissions via custom roles, groups, or project/environment admin assignments

A user with the _User_ organisation role can still have significant access — for example, they could be an administrator of specific projects or environments while having no access to others.

#### Project and environment administrators

In addition to organisation-level roles, Flagsmith has built-in administrator permissions at the project and environment levels:

- _Project Administrator_ — full access to a specific project and all its environments
- _Environment Administrator_ — full access to a specific environment only

These are assigned per-resource, not globally. For example, a user could be:

- An _Organisation User_ (no organisation-wide admin access)
- A _Project Administrator_ for _Mobile App_ (full control of that project and all of its environments)
- An _Environment Administrator_ for _Development_ in _Web App_ (full control of just that environment)

This granular approach allows you to give users administrative control exactly where they need it, without granting organisation-wide access.

#### Custom roles

**Custom roles** can be assigned to users, groups or [Admin API](/integrating-with-flagsmith/flagsmith-api-overview/admin-api) keys. Any
number of custom roles can be created and assigned.

Creating, modifying or assigning roles requires organisation administrator permissions.

### Groups

A group is a collection of users. If a custom role is assigned to a group, the role's permissions will be granted to all
group members. Users can belong to any number of groups.

Creating or modifying existing groups requires organisation administrator permissions.

Permissions to add or remove users from groups can be granted in two ways:

- The _manage group membership_ permission allows modifying any group's membership
- A _group admin_ can manage membership only for that group

## Add users to your organisation

You can add users to your organisation by sending them an invitation email from Flagsmith, or by sharing an invitation
link directly with them. Both options require organisation administrator permissions, and are available from **Users and
Permissions > Members**.

Users can also join your organisation directly by logging in to Flagsmith using
[single sign-on](/administration-and-security/access-control/saml).

### Email invites

:::info

If you are self-hosting Flagsmith, you must
[configure an email provider](/deployment-self-hosting/core-configuration/email-setup) before using email invites.

:::

To send invitation emails to specific users, click on **Invite members**. Then, fill in the email address and built-in
role of each user you want to invite. You can also add these users to any groups at this time, so that they have the 
permissions they need as soon as they log in for the first time.

When a user accepts their email invitation, they will be prompted to sign up for a Flagsmith account, or they can choose
to log in if they already have an account with the same email address.

Users who have not yet accepted their invitations are listed in the _Pending invites_ section at the bottom of this
page. From here you can also resend or revoke any pending invitations.

### Invitation links

:::warning

Anyone with an invitation link can join your Flagsmith organisation at any time. Share these links with caution and
regenerate them if they are compromised.

:::

Direct links to join your organisation can be found in the **Team Members** section of this page. One direct link is
available for each built-in role that users will have when joining your organisation.

## Provision permissions

If a user joins your organisation with the built-in _User_ role, they will not have any permissions to view or change
anything in your Flagsmith organisation. You can provide default fine-grained permissions to users with any of these
options:

- Add users by default to a group. When creating or editing a group, select the **Add new users by default** option.
  When a user logs in for the first time to your organisation, they will automatically be added to all groups that have
  this option enabled.
- [Use existing groups from your enterprise identity provider](/administration-and-security/access-control/saml#using-groups-from-your-saml-idp).
  Any time a user logs in using single sign-on, they will be made a member of any groups with matching external IDs.

## Tagged permissions

Some permissions can be restricted to features with specific tags. For example, you can configure a role to create change requests only for features tagged with _marketing_.

The _Supports Tags_ column in the tables below indicates which permissions support tag-based restrictions. See [Tags](/managing-flags/tagging) for how to create and manage tags.

## Permissions reference

Permissions can be assigned at four levels: user group, organisation, project, and environment.

### User group

| Permission  | Ability                                          |
| ----------- | ------------------------------------------------ |
| Group Admin | Allows adding or removing users from this group. |

### Organisation

| Permission         | Ability                                                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Create project     | Allows creating projects in the organisation. Users are automatically granted Administrator permissions on any projects they create. |
| Manage user groups | Allows adding or removing users from any group.                                                                                      |

### Project

| Permission         | Ability                                                                                                                                      | Supports Tags |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| Administrator      | Grants full read and write access to all environments, features, and segments.                                                               |               |
| View project       | Allows viewing this project. The project is hidden from users without this permission.                                                       |               |
| Create environment | Allows creating new environments in this project. Users are automatically granted Administrator permissions on any environments they create. |               |
| Create feature     | Allows creating new features in all environments.                                                                                            |               |
| Delete feature     | Allows deleting features from all environments.                                                                                              | Yes           |
| Manage segments    | Grants write access to segments in this project.                                                                                             |               |
| View audit log     | Allows viewing all audit log entries for this project.                                                                                       |               |

### Environment

| Permission               | Ability                                                                                                                  | Supports Tags |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------ | ------------- |
| Administrator            | Grants full read and write access to all feature states, overrides, identities, and change requests in this environment. |               |
| View environment         | Allows viewing this environment. The environment is hidden from users without this permission.                           |               |
| Update feature state     | Allows updating any feature state or values in this environment.                                                         | Yes           |
| Manage identities        | Grants read and write access to identities in this environment.                                                          |               |
| Manage segment overrides | Grants write access to segment overrides in this environment.                                                            |               |
| Create change request    | Allows creating change requests for features in this environment.                                                        | Yes           |
| Approve change request   | Allows approving or denying change requests in this environment.                                                         | Yes           |
| View identities          | Grants read-only access to identities in this environment.                                                               |               |

### Permission levels explained

Some permissions are **project-level** and cannot be restricted to specific environments. This follows directly from the [Flagsmith data model](/flagsmith-concepts/data-model): features and segments are defined at the project level and shared across all environments.

- **Create feature** — New features appear in all environments simultaneously
- **Delete feature** — Removing a feature removes it from all environments simultaneously
- **Manage segments** — Segments are project-wide and affect all environments

To control **flag values** per environment, use environment-level permissions like _Update feature state_ and _Manage segment overrides_.

## Common permission setups

The following scenarios illustrate how to configure permissions for typical team structures. These examples help clarify which permissions to set at the project level versus the environment level.

:::note

These examples assume users have the built-in _User_ role at the organisation level (not _Organisation Administrator_). Organisation Administrators have full access to everything, so granular permissions only apply to users with the _User_ role.

:::

### Developer with Production restrictions

**Goal**: Alice (developer) can create features and work freely in Development and Staging, but cannot modify Production directly — she must submit change requests instead.

**Setup**:

1. Create a _Developers_ group and add Alice to it
2. Create a custom role called _Developer Access_ with these permissions:
   - **Project-level**: View project, Create feature
   - **Development environment**: Administrator
   - **Staging environment**: Administrator
   - **Production environment**: View environment, Create change request
3. Assign the _Developer Access_ role to the _Developers_ group

**Result**: Alice can create features (which appear in all environments), toggle them freely in Development and Staging, but must submit change requests to modify anything in Production.

### QA team with read-only Production access

**Goal**: The QA team can view Production flag states and identities for verification, but cannot change anything.

**Setup**:

1. Create a _QA Team_ group and add QA team members to it
2. Create a custom role called _Production Viewer_ with these permissions:
   - **Project-level**: View project
   - **Production environment**: View environment, View identities
3. Assign the _Production Viewer_ role to the _QA Team_ group

**Result**: QA team members can see the Production environment and inspect identities, but cannot modify flag states or create change requests. The _Production Viewer_ role can also be assigned to other groups (e.g., _Auditors_) that need the same access.

:::note Why QA cannot have environment-specific segment access

You might want QA to view segments in Production only. However, _Manage segments_ is a **project-level permission** — granting it would give QA segment control across all environments. Segments are defined once per project and shared across all environments.

:::

### Restricting feature deletion

**Goal**: Prevent most developers from accidentally deleting features while allowing team leads to do so when necessary.

**Understanding**: _Delete feature_ is a **project-level permission**. Deleting a feature removes it from **all environments simultaneously** — there is no way to delete a feature from just one environment.

**Setup**:

1. Create a custom role called _Feature Creator_ with:
   - **Project-level**: View project, Create feature (but **not** Delete feature)
   - Environment permissions as needed
2. Create a custom role called _Feature Manager_ with:
   - **Project-level**: View project, Create feature, Delete feature
   - Environment permissions as needed
3. Assign the _Feature Creator_ role to the _Developers_ group (or other groups that need to create features)
4. Assign the _Feature Manager_ role to team leads or a _Team Leads_ group

**Result**: Most developers can create and modify features, but only those with the _Feature Manager_ role can delete them. Multiple groups can share the same role.

### Team lead with full project control

**Goal**: A team lead needs complete control over their project, including all environments, but should not affect other projects in the organisation.

**Setup**:

1. Create a custom role called _Project Admin_ with:
   - **Project-level**: Administrator
2. Assign the _Project Admin_ role to the team lead user (or to a _Team Leads_ group)

**Result**: The team lead has full access to all environments, features, and segments within that project. They can manage permissions for other users on that project. They cannot access other projects unless explicitly granted. The same _Project Admin_ role can be reused across different projects for different team leads.

### External contractor with limited access

**Goal**: An external contractor needs to work on a specific feature in Development only, with no access to Production data.

**Setup**:

1. Create a custom role called _Dev Environment Editor_ with:
   - **Project-level**: View project
   - **Development environment**: View environment, Update feature state
2. Assign the _Dev Environment Editor_ role to the contractor user (or to a _Contractors_ group if you have multiple)
3. Optionally, use [tagged permissions](#tagged-permissions) to restrict their access to only features with a specific tag (e.g., _contractor-feature_)

**Result**: The contractor can see the project structure and modify flag states in Development only. They cannot see or affect Staging, Production, or any identities. This role could also be useful for interns or other users who should only work in Development.

## Deprecated features

Groups can grant permissions directly to their members in the same way that roles do. This functionality was deprecated
in Flagsmith 2.137.0. To grant permissions to all members of a group, create a role with the desired permissions and
assign it to the group instead.

Assigning roles to groups has several benefits over assigning permissions directly to a group:

- Roles can be assigned to Admin API keys, but Admin API keys cannot belong to groups.
- If you need multiple groups or users with similar permissions, the common permissions can be defined in a role and
  assigned to multiple groups or users instead of being duplicated.
- Having roles as the single place where permissions are defined makes auditing permissions easier.
