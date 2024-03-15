---
title: Role Based Access Control
---

Flagsmith provides fine-grained permissions to help larger teams manage access and roles across organisations, projects
and environments.

:::info

The Permissions/Role Based Access features of Flagsmith are _not_ part of the Open Source version. If you want to use
these features as part of a self hosted/on premise solution, please [get in touch](https://flagsmith.com/contact-us/).

:::

## Users, Groups, and Roles

Permissions can be assigned to Flagsmith individual users, groups, or roles.

### Users

Flagsmith Users can be defined as Organisation Administrators or Users. Organisation Administrator is effectively a
super-user role, and gives full read/write access to every Project, Environment, Flag, Remote Config and Segment within
that Organisation.

Users that are not Organisation Administrators must have permissions assigned to them manually at the relevant levels.

### Groups

Groups are a convenient way to manage permissions for multiple Flagsmith users. Groups can contain any number of
Flagsmith users. You can create groups with the Organisation Settings page.

Members of a group can be designated as an admin for that group. As a group admin, users can manage the membership for
that group, but not the permissions the group has on other entities.

### Roles

A _Role_ is an entity to which you can attach a set of permissions. Permissions can allow privileges at Organization,
Project, and Environment levels. You can assign a role, along with its associated permissions, to a User or Group. You
will also be able to assign API keys to a Role in future versions.

#### Creating a Role

You can create a Role in the Organisation Settings page.

#### Add Permissions to a Role

Once the role is created you can assign the corresponding permissions.

**E.g. Add Project permission:**

- Choose a Role.
- Go to the Projects tab.
- Select a Project and enable the relevant permissions.

### Assign Role to Users or Groups

After creating the Role, you can assign it to Users or Groups.

**E.g. Assign role to a user:**

- Choose a role.
- Go to the Members tab.
- Select the Users tab.
- Click assign role to user button and select a user.

## Permissions

Permissions can be assigned at 3 levels: Organisation, Project, and Environment.

### Organisation

| **Permission**     | **Ability**                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| Create Project     | Allows the user to create Projects in the given Organisation                |
| Manage User Groups | Allows the user to manage the Groups in the Organisation and their members. |

### Project

| **Permission**     | **Ability**                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------ |
| Administrator      | Full Read/Write over all Environments, Feature Flag, Remote Config, Segment and Tag values |
| View Project       | Can view the Project within their account                                                  |
| Create Environment | Can create new Environments within the Project                                             |
| Create Feature     | Can create a new Feature / Remote Config                                                   |
| Delete Feature     | Can remove an existing Feature / Remote Config entirely from the Project                   |
| Manage Segments    | Can create, delete and edit Segments within the Project                                    |
| View audit log     | Allows the user to view the audit logs for this Project.                                   |

### Environment

| **Permission**           | **Ability**                                                     |
| ------------------------ | --------------------------------------------------------------- |
| Administrator            | Can modify Feature Flag, Remote Config and Segment values       |
| View Environment         | Can see the Environment within their account                    |
| Update Feature State     | Update the state or value for a given feature                   |
| Manage Identities        | View and update Identities                                      |
| Manage Segment Overrides | Permission to manage segment overrides in the given environment |
| Create Change Request    | Creating a new Change Request                                   |
| Approve Change Request   | Approving or denying existing Change Requests                   |
| View Identities          | Viewing Identities                                              |
