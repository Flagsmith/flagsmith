---
title: Tagging
sidebar_label: Tagging
sidebar_position: 2
---

You can create tags within Flagsmith and tag feature flags in order to organise them. Tags can also be used to filter the list of feature flags in the event that you have a large number of them.

This guide explains how to create and apply tags to feature flags within Flagsmith, as well as some tagging good practices and conventions.

---

## Creating and Applying Tags

You can add tags to feature flags during creation or when editing an existing flag.

### When Creating a Feature Flag

1. Go to the **Features** section in your dashboard.
2. Click **Create Feature**.
3. Fill in the feature flag details. In the **Tags** field (optional), enter one or more tags to organise your feature flag. You can also add special tags such as `protected` to prevent accidental deletion.
4. Click **Create Feature** to save your changes.

### When Editing a Feature Flag

1. In the **Features** section, select the feature flag you want to edit.
2. Go to the **Settings** tab.
3. In the **Tags** field, add or remove tags as needed.
4. Click **Update Settings** to save your changes.

You can quickly find and manage feature flags by using the **tag filter** in the Features list to display only feature flags with specific tags. This is especially useful for large projects with many feature flags.

---

## Tag Conventions

- **General Recommendations:**
  - Use clear, descriptive tag names (e.g., `beta`, `deprecated`, `marketing`).
  - Establish a naming convention for your team. For example, use all lowercase, hyphen-separated tags.
  - Avoid using case-sensitive tags unless necessary. By default, tags are not case-sensitive.

:::info Protected Tags

Tags with the following names will prevent users from being able to delete tagged feature flags via the dashboard:

- `protected`.
- `donotdelete`.
- `permanent`.

:::


---

## Best Practices for Tag Management
- Use tags to group related feature flags (e.g., by feature, team, or release).
- Apply protected tags (`protected`, `donotdelete`, `permanent`) to critical or long-lived feature flags to prevent accidental deletion.
- Regularly review and update tags to keep your feature flag management organised.

---

## What's Next

- Learn how to configure [tag-based permissions for roles](/administration-and-security/access-control/rbac).
- See more advanced [feature flag management](/managing-flags/core-management) techniques.

