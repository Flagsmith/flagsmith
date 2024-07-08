---
title: Custom Fields
sidebar_position: 110
---

Flagsmith allows certain Entities within a Project to have custom fields of different types.

## Core Entities that support Custom Fields

- **[Features](/basic-features/managing-features#use-custom-fields)**.
- **[Environment](/system-administration/environment-settings#custom-fields)**.
- **[Segments](/basic-features/segments#use-custom-fields)**.

## Custom Fields

To be able to add Custom Fields to your Entities, you first need to define them within Project Settings -> Custom
Fields.

Here you'll also need to define whether it's optional or required.

- **Optional**: You may or may not add Custom Fields to your Entities.
- **Required**: You won't be able to update or create an Entity within your Project unless you include this Custom
  Field.

![Image](/img/custom-fields/custom-fields.png)

### Types of Custom Field

Custom Fields supports five primary types of values, each serving distinct purposes:

**String**: A basic data type representing text or alphanumeric characters. Strings are versatile and can describe a
wide range of attributes or characteristics.

**URL**: A type specifically designed to store web addresses or Uniform Resource Locators.

**Integer**: A numeric data type representing whole numbers without decimal points. Integers are useful for quantifiable
properties or attributes.

**Multiline String**: Similar to a standard string but capable of storing multiline text. Multiline strings are
beneficial for longer descriptions or content blocks.

**Boolean**: A data type with only two possible values: true or false. Booleans are ideal for representing binary
attributes or conditions.
