---
title: Core Management
sidebar_label: Core Management
sidebar_position: 1
---

Flags in Flagsmith are used to categorise and monitor user actions or events, such as detecting spam or abuse. This guide covers how to create, edit, clone, and delete flags in your project.

---

## Creating a Flag

To create a new feature flag:

1. Go to the **Features** section in your dashboard.
2. Click **Create Feature**.
3. Enter a descriptive name for your flag (e.g., `new_ui_enabled`).
4. Fill in the available fields according to the specifications of your feature. Note that these values are applied to all your [environments]. You can edit each environment individually later.
    - **Enabled by default**: determines the initial state of the flag for all environments. This can be edited for each environment later.
    - **Value** (optional): additionally to their boolean value, you can choose a format and a value for your flag.
    - **Tags** (optional): organise your flags by tags or add `protected` to prevent them from accidentally being deleted.
    - **Description** (optional): add a feature flag description.
    - **Server-side only**: enabling this prevents your flag from being accessed by client-side SDKs.
5. Click **Create Feature**.

:::tip

By clicking the **Create A/B/n Test** button, you can define values for A/B testing. To learn more about this operation, refer to the [A/B Testing guide](../advanced-use/ab-testing).

:::

---

## Editing a Flag

You create feature flags once per project, but you edit them within each environment. To edit an existing flag:

1. While on the **Environments** tab on the dashboard, use the dropdown to select the environment where you want to apply the changes.
2. Locate the feature flag you want to edit and click on it. You can use the search bar to find the flag by its name.

:::tip

If you just want to toggle the feature flag *on* or *off*, use the switch under the **View** column in the list view.

:::

3. On the **Value** tab, you can set the flag to be on or off, as well as edit a value for it. Click **Update Feature Value** to save your changes.
4. Optionally, create segment-specific features and define **Segment Overrides**. Refer to the documentation to learn more about [Segments](../basic-features/segments.md). Save any changes by clicking the **Update Segment Overrides** button.
5. On the **Settings** tab, you can:
    - Add tags to your feature flag.
    - Assign it to specific *users* and *groups*.
    - Update the flag's description.
    - Mark the flag as **Server-side only** to prevent it from being accessed by client-side SDKs.
    - Set the **Archived** status to filter the flag as no longer relevant. Note that the flag will still be returned by the endpoint as before.
  Click **Update Settings** to save your changes.

:::tip

Changes made in the **Settings** tab affect all environments. Changes made in other tabs while editing a feature flag are valid only for the selected environment.

:::

---

## Deleting a Flag

To delete a feature flag:

1. In the **Features** section, locate the flag you want to remove and click the **three dots** icon on the right.
2. Select the **Remove feature** option.
3. Type in the name of the feature to confirm the deletion.

:::caution

Deleting a flag is permanent and cannot be undone. Make sure your applications do not contain any reference to this feature before confirming deleting it.

:::

---

## Troubleshooting

### Flags Not Updating

- Make sure you have saved your changes in each tab of the edit feature flag panel.
- Check that you are in the correct project and environment.

### Permission Issues

- You may need additional permissions to create, edit, clone, or delete flags. If you see permission errors or options are disabled, contact your Flagsmith administrator to review your access rights. For more information, see the [Permissions and Roles](../system-administration/rbac.md) page.
