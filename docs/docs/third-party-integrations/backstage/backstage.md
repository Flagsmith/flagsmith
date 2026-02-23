---
title: Backstage
sidebar_position: 50
description: 'Integrate Flagsmith feature flags into your Backstage developer portal'
---

The [Flagsmith Backstage Plugin](https://github.com/Flagsmith/flagsmith-backstage-plugin) brings feature flag management
directly into your [Backstage](https://backstage.io/) developer portal. It provides three components:

- **Feature Flags Tab** — A full flag list with environment states, tags, and toggle status.
- **Overview Card** — A quick summary of your feature flags for entity overview pages.
- **Usage Card** — A chart showing flag usage metrics over time.

![Backstage Plugin Components](/img/integrations/backstage/components-overview.png)

## Prerequisites

- A running [Backstage](https://backstage.io/) instance.
- A Flagsmith account with an **Admin API Key**.
- Your Flagsmith **Project ID** and **Organisation ID**.

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

### Overview Card

Add the `FlagsmithOverviewCard` to your entity overview page:

```tsx
import { FlagsmithOverviewCard } from '@flagsmith/backstage-plugin';

// Inside your overview grid:
<Grid item md={6}>
  <FlagsmithOverviewCard />
</Grid>
```

<img src="/img/integrations/backstage/overview-card.png" alt="Overview Card" width="600" />

### Usage Card

Add the `FlagsmithUsageCard` to display flag usage metrics:

```tsx
import { FlagsmithUsageCard } from '@flagsmith/backstage-plugin';

// Inside your overview grid:
<Grid item md={6}>
  <FlagsmithUsageCard />
</Grid>
```

<img src="/img/integrations/backstage/usage-card.png" alt="Usage Card" width="600" />

## Entity Annotations

Annotate your entities in `catalog-info.yaml` so the plugin knows which Flagsmith project to display:

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: my-service
  annotations:
    flagsmith.com/project-id: '<YOUR_PROJECT_ID>'
    flagsmith.com/org-id: '<YOUR_ORG_ID>'
spec:
  type: service
  owner: my-team
  lifecycle: production
```

| Annotation                 | Required | Description                                                        |
| -------------------------- | -------- | ------------------------------------------------------------------ |
| `flagsmith.com/project-id` | Yes      | The numeric ID of your Flagsmith project.                          |
| `flagsmith.com/org-id`     | Yes      | The numeric ID of your Flagsmith organisation.                     |

## Getting Your Credentials

### Admin API Key

1. Log in to [Flagsmith](https://app.flagsmith.com/).
2. Navigate to **Account Settings > Keys**.
3. Copy your **Admin API Key**.

### Project ID

1. Open your Flagsmith project.
2. Go to **Project Settings**.
3. The **Project ID** is displayed at the top of the settings page.

### Organisation ID

1. Navigate to **Organisation Settings**.
2. The **Organisation ID** is displayed at the top of the settings page.
