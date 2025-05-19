---
title: Custom Fields
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip
Custom fields are part of our [Enterprise plans](/version-comparison#enterprise-benefits).
:::

## Overview

Store additional information alongside Flagsmith entities to improve traceability and management. Common use cases:

- Link flags to issue tracker tickets
- Connect segments with analytics platform configurations
- Add detailed environment descriptions

Custom fields can be added to [flags](/basic-features/managing-features.md), [segments](/basic-features/segments.md), and [environments](/basic-features#environments).

## Field Types and Validation

| Type | Description | Validation Rules | Example |
|------|-------------|-----------------|----------|
| String | Single line of text | Maximum 1000 characters | `"release-2.1"` |
| Multi-line string | Multiple lines of text | Maximum 10000 characters | `"Detailed\ndescription"` |
| Integer | Whole numbers | No decimal points | `42` |
| Boolean | True/false values | Must be true/false | `true` |
| URL | Valid web URLs | Must include scheme | `https://flagsmith.com` |

:::caution URL Validation
URLs require explicit schemes - `https://flagsmith.com` is valid, but `/example/foo` is not.
Validation uses Python's [urlparse](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse).
:::

## Permissions

<details>
<summary>Access Requirements</summary>

| Action | Required Permission |
|--------|-------------------|
| Define Fields | Administrator |
| Update Values | Entity Edit Access |

For a complete list of available permissions, see the [permissions reference](/system-administration/rbac#permissions-reference).


</details>

## Managing Custom Fields

### Creating Fields

1. Navigate to **Organisation Settings > Custom Fields**
2. Configure field properties:
   - Name (displayed to users)
   - Description (field purpose)
   - Type (from table above)
   - Associated Entities
   - Required/Optional status

### Entity Association

Custom fields can be associated with:

<Tabs>
<TabItem value="features" label="Features">

- Link to issue trackers
- Store product codes
- Track release versions

</TabItem>
<TabItem value="segments" label="Segments">

- Analytics platform IDs
- User cohort descriptions
- Business unit associations

</TabItem>
<TabItem value="environments" label="Environments">

- Infrastructure details
- Deployment regions
- Support contact info

</TabItem>
</Tabs>

### Field Requirements

- Make fields required or optional per entity type
- Example: Required for features, optional for segments
- Enforced during creation/updates

## API Integration

:::info
Custom fields are accessible through the [Flagsmith Admin API](/clients/rest#private-admin-api-endpoints)
:::

<details>
<summary>Example API Responses</summary>

```json
{
  "metadata": [
    {
      "id": 123,
      "model_field": 128,
      "field_value": "https://example.com/FOO-123"
    }
  ]
}
```

See [API Documentation](https://api.flagsmith.com/api/v1/docs/#/api/api_v1_projects_features_read) for complete details.
</details>

## Consuming Custom Fields

Custom fields are primarily designed for human readability in the Flagsmith dashboard, typically serving traceability and accountability purposes.

:::info Implementation Note
Custom field values belong to the features themselves, not to environment feature states. You cannot override these values in different environments, segments, or identities.
:::

### API Access

Custom fields are accessible through two main endpoints:

<Tabs>
<TabItem value="features" label="Feature Metadata">

```bash
curl "https://api.flagsmith.com/api/v1/projects/YOUR_PROJECT_ID/features/YOUR_FEATURE_ID/" \
  -H "Authorization: Api-Key YOUR_API_KEY"
```

Response includes metadata with custom field values:

```json
{
  "metadata": [
    {
      "id": 123,
      "model_field": 128,
      "field_value": "https://example.com/FOO-123"
    },
    {
      "id": 124,
      "model_field": 129,
      "field_value": "Example Team"
    }
  ]
}
```

</TabItem>
<TabItem value="definitions" label="Field Definitions">

```bash
curl "https://api.flagsmith.com/api/v1/organisations/YOUR_ORGANISATION_ID/metadata-model-fields/" \
  -H "Authorization: Api-Key YOUR_API_KEY"
```

Response includes field definitions:

```json
{
 "count": 2,
 "next": null,
 "previous": null,
 "results": [
  {
   "id": 178,
   "name": "Ticket URL",
   "type": "url",
   "description": "URL to ticket in our issue tracker",
   "organisation": 15467
  },
  {
   "id": 179,
   "name": "Product code",
   "type": "int",
   "description": "Product code associated with this feature",
   "organisation": 15467
  }
 ]
}
```

</TabItem>
</Tabs>

:::caution
Custom field values are not returned to applications that consume flags through the standard SDK endpoints.
:::

## Important Notes

:::warning
- Field data types are only validated on save
- Type changes don't modify existing data
- Deleting fields removes all associated data
:::
