---
title: Metadata
sidebar_position: 110
---

Flagsmith allows certain Entities within a Project to have Metadata of different types.

## Core Entities that support Metadata

- **[Features](/basic-features/managing-features#use-metadata)**.
- **[Environment](/system-administration/environment-settings#use-metadata)**.
- **[Segments](/basic-features/segments#use-metadata)**.

## Metadata Fields

To be able to add Metadata to your Entities, you first need to create Metadata fields within Project Settings ->
Metadata.

Here you'll also need to define whether it's optional or required.

- **Optional**: You may or may not add Metadata to your Entities.
- **Required**: You won't be able to update or create an Entity within your Project unless you include this Metadata.

![Image](/img/metadata/metadata-fields.png)

### Types of Metadata Field

Metadata Field supports five primary types of metadata values, each serving distinct purposes:

**String**: A basic data type representing text or alphanumeric characters. Strings are versatile and can describe a
wide range of attributes or characteristics.

**URL**: A type specifically designed to store web addresses or Uniform Resource Locators.

**Integer**: A numeric data type representing whole numbers without decimal points. Integers are useful for quantifiable
properties or attributes.

**Multiline String**: Similar to a standard string but capable of storing multiline text. Multiline strings are
beneficial for longer descriptions or content blocks.

**Boolean**: A data type with only two possible values: true or false. Booleans are ideal for representing binary
attributes or conditions.
