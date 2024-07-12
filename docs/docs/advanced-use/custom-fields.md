---
title: Custom Fields
---

:::info

Custom fields are available on [Enterprise plans](/version-comparison.md#enterprise-benefits).

Custom fields were introduced in Flagsmith [2.116.0](https://github.com/Flagsmith/flagsmith/releases/tag/v2.116.0).

:::

![](/img/metadata/metadata-example.png)

As your usage of feature flags grows, it helps to store additional information alongside different Flagsmith entities.
For example, you might want to:

- Relate every flag to a ticket in your issue tracker so that everyone knows what a flag does and what state of
  development it is in.
- Add a link from Flagsmith segments to the corresponding segments in your analytics platform.
- Add a detailed description to your Flagsmith environments.

You can define **custom fields** that are shown when creating or modifying
[**flags**](/basic-features/managing-features.md), [**segments**](/basic-features/segments.md) or
[**environments**](/basic-features#environments). Custom fields are defined per [project](/basic-features#projects).

## Permissions

Defining custom fields requires administrator permissions for a given project.

Updating the values of custom fields requires edit permissions for the given entity.

## Defining custom fields

Custom fields can be defined in **Project Settings > Custom Fields**.

Custom fields have the following properties:

- **Name**: the visible name of the field as it will be presented to users.
- **Description**: a short description of what the field is for. It is only shown when editing custom field definitions.
- **Type**: validates this field's data when saving to be one of the following types:
  - **String**: A single line of text.
  - **Multi-line string**: One or more lines of text.
  - **Integer**: Whole numbers without a decimal point.
  - **Boolean**: A binary choice between true or false.
  - **URL**: An absolute URL with an explicit scheme as defined by Python's
    [urlparse](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse) function. For example,
    `https://flagsmith.com` is considered valid but `/example/foo` is not.
- **Entities**: Which Flagsmith entities to display these fields for during creation or editing. The following options
  are allowed:
  - Features
  - Segments
  - Environments
- **Required**: Lets you choose whether a field is required for each entity it is associated with. For example, you
  could make a ticket URL required for features but optional for segments.

## Modifying existing fields

Field data types are only validated when saving. Modifying existing field data types will not delete or modify existing
data.

Changing an optional field into a required field will prevent you from creating or updating the relevant entities
without providing a value for that field.

Deleting custom fields will also delete all data associated with that field.
