---
title: How to Use Feature Flag Tags
description: A practical guide to creating, applying and managing tags for feature flags
---

# How to Use Feature Flag Tags

This guide shows you how to use tags to organize and manage your feature flags in Flagsmith. Tags help maintain order as your feature flag count grows and ensure important flags are protected.

## Creating and Applying Tags

### Basic Tag Management
1. Navigate to the Flags page
2. Create new tags or select existing ones
3. Apply tags to flags based on their purpose

### Common Tag Categories
- **Lifecycle**: `temporary`, `permanent`, `experimental`
- **Purpose**: `kill-switch`, `ab-test`, `config`
- **Team**: `frontend`, `backend`, `mobile`
- **Status**: `archived`, `active`, `deprecated`

## Protected Tag Conventions

### Reserved Tags
The following tags prevent flag deletion via the dashboard:
- `protected`
- `donotdelete`
- `permanent`

### When to Use Protected Tags
- Critical kill switches
- Core feature toggles
- Configuration flags
- Platform-wide settings

## Organizing with Tags

### Filtering and Search
- Use tags to filter the flag list
- Combine multiple tags for precise filtering
- Search within tagged groups

### Tag-Based Organization
- Group flags by feature area
- Categorize by development stage
- Mark temporary vs permanent flags

## Best Practices

### Naming Conventions
- Use lowercase for consistency
- Choose clear, descriptive names
- Follow team-wide conventions

### Tag Management
- Regular tag cleanup
- Document tag purposes
- Consistent usage across teams

### Protection Strategy
- Tag critical flags appropriately
- Review protected flags regularly
- Document protection reasoning

:::tip
Use tags to implement a flag cleanup strategy - regularly review flags with `temporary` or `experimental` tags for potential removal.
:::

For more on flag archiving and management, see [Core Management](./core-management).