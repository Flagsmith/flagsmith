---
title: Role Based Access Control
---

Flagsmith provides fine-grained permissions to help larger teams manage access and roles across projects and
environments.

Permissions are assigned to individual team members or to groups.

:::info

The Permissions/Role Based Access features of Flagsmith are _not_ part of the Open Source version. If you want to use
these features as part of a self hosted/on premise solution, please [get in touch](https://flagsmith.com/contact-us/).

:::

## Groups

Groups are a convenient way to manage permissions for multiple team members. Groups can contain any number of team
members. You can create groups with the Organisation Settings page.

Members of a group can be designated as an admin for that group. As a group admin, users can manage the membership for
that group, but not the permissions the group has on other entities.

## Organisations

Team members can be defined as Organisation Administrators or Users. Organisation Administrator is effectively a
super-user role, and gives full read/write access to every Project, Environment, Flag, Remote Config and Segment within
that Organisation.

Users that are not Organisation Administrators must have permissions assigned to them manually at the relevant levels.
The permissions available at the Organisation level are defined below.

| **Role**           | **Ability**                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| Create Project     | Allows the user to create Projects in the given Organisation                |
| Manage User Groups | Allows the user to manage the Groups in the Organisation and their members. |

## Projects

Team Members and Groups can be given individual roles at a Project level.

| **Role**           | **Ability**                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------ |
| Administrator      | Full Read/Write over all Environments, Feature Flag, Remote Config, Segment and Tag values |
| View Project       | Can view the Project within their account                                                  |
| Create Environment | Can create new Environments within the Project                                             |
| Create Feature     | Can create a new Feature / Remote Config                                                   |
| Delete Feature     | Can remove an existing Feature / Remote Config entirely from the Project                   |
| Manage Segments    | Can create, delete and edit Segments within the Project                                    |
| View audit log     | Allows the user to view the audit logs for this Project.                                   |

## Environments

Team Members and Groups can be given individual roles at an Environment level.

| **Role**               | **Ability**                                               |
| ---------------------- | --------------------------------------------------------- |
| Administrator          | Can modify Feature Flag, Remote Config and Segment values |
| View Environment       | Can see the Environment within their account              |
| Update Feature State   | Update the state or value for a given feature             |
| Manage Identities      | View and update Identities                                |
| Create Change Request  | Creating a new Change Request                             |
| Approve Change Request | Approving or denying existing Change Requests             |
| View Identities        | Viewing Identities                                        |
