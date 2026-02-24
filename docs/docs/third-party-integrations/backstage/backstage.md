---
title: Backstage
sidebar_position: 50
description: 'Integrate Flagsmith feature flags into your Backstage developer portal'
---

The [Flagsmith Backstage Plugin](https://github.com/Flagsmith/flagsmith-backstage-plugin) brings feature flag observability
directly into your [Backstage](https://backstage.io/) developer portal. It provides three components:

- **Feature Flags Tab** — A full-page table listing all flags, with their environment states, tags, and status.
- **Overview Card** — A quick summary of your feature flags for entity overview pages.
- **Usage Card** — A chart showing flag usage metrics over time.

![Backstage Plugin Components](/img/integrations/backstage/components-overview.png)

## Prerequisites

- A running [Backstage](https://backstage.io/) instance.
- A Flagsmith account with an **Admin API Key**.
- Your Flagsmith **Project ID**.

## Installation

Install the plugin from your Backstage app root:

```bash
yarn --cwd packages/app add @flagsmith/backstage-plugin
```

## Configuration

Add the Flagsmith proxy configuration to your `app-config.yaml`:

```yaml
proxy:
  endpoints:
    '/flagsmith':
      target: 'https://api.flagsmith.com/api/v1'
      headers:
        Authorization: Api-Key ${FLAGSMITH_API_TOKEN}
```

:::tip

If you are self-hosting Flagsmith, replace the `target` URL with your own Flagsmith API address, e.g.
`https://flagsmith.example.com/api/v1`.

:::

## Adding Components to Entity Pages

Edit your `packages/app/src/components/catalog/EntityPage.tsx` to add the Flagsmith components.

### Feature Flags Tab

Import and add the `FlagsTab` as a new tab on your entity page:

```tsx
import { FlagsTab } from '@flagsmith/backstage-plugin';

// Inside your entity page layout, add a new tab:
<EntityLayout.Route path="/feature-flags" title="Feature Flags">
  <FlagsTab />
</EntityLayout.Route>
```

![Feature Flags Tab](/img/integrations/backstage/flags-tab.png)

![Flag Details Expanded](/img/integrations/backstage/flag-details-expanded.png)

### Overview Card

Add the `FlagsmithOverviewCard` to your entity overview page:

```tsx
import { FlagsmithOverviewCard } from '@flagsmith/backstage-plugin';

// Inside your overview grid:
<Grid item md={6}>
  <FlagsmithOverviewCard />
</Grid>
```

![Overview Card](/img/integrations/backstage/overview-card.png)

### Usage Card

Add the `FlagsmithUsageCard` to display flag usage metrics:

```tsx
import { FlagsmithUsageCard } from '@flagsmith/backstage-plugin';

// Inside your overview grid:
<Grid item md={6}>
  <FlagsmithUsageCard />
</Grid>
```

![Usage Card](/img/integrations/backstage/usage-card.png)

## Entity Annotations

Annotate your entities in `catalog-info.yaml` so the plugin knows which Flagsmith project to display:

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: my-service
  annotations:
    flagsmith.com/project-id: '<YOUR_PROJECT_ID>'
spec:
  type: service
  owner: my-team
  lifecycle: production
```

| Annotation                 | Required | Description                                   |
| -------------------------- | -------- | --------------------------------------------- |
| `flagsmith.com/project-id` | Yes      | The numeric ID of your Flagsmith project.     |

## Getting Your Credentials

### Admin API Key

1. Log in to [Flagsmith](https://app.flagsmith.com/).
2. Navigate to **Organisation Settings → API Keys**.
3. Click **Create API Key** and ensure **Is admin** is enabled.
4. Copy your **Admin API Key**.

### Project ID

1. Open your Flagsmith project.
2. Go to **Project Settings → General**.
3. In the **JSON data** dropdown at the top, select **Project**.
4. The **Project ID** is the numeric `id` value (not the `uuid`). For example, if you see `"id": 1`, your Project ID is `1`.

:::note

You may need to enable **JSON references** in your **Account Settings** to see the JSON data dropdown.

:::
