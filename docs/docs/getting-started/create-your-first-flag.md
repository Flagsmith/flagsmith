---
title: Create Your First Flag
sidebar_position: 1
sidebar_label: Create Your First Flag
---

import Admonition from '@theme/Admonition';

# Create Your First Flag

This tutorial will guide you through creating your first feature flag in Flagsmith and using it in your application.

<Admonition type="tip" title="What is a Feature Flag?">
A feature flag is a toggle to enable or disable a feature in your application without deploying new code. Learn more in the [Feature Flags](./feature-flags.md) page.
</Admonition>

## 1. Create an account with Flagsmith

To get started, [sign up at Flagsmith.com](https://app.flagsmith.com/signup) and create your first Organisation and Project.

![Create Organisation](/img/quickstart/demo_create_1.png)

Next, create a Project:

![Create Project](/img/quickstart/demo_create_2.png)

<Admonition type="info" title="Flagsmith Data Model">
Flagsmith organises Projects into Environments. When you create a Project, `Development` and `Production` Environments are created automatically. See the [Data Model](./data-model.md) for more details.
</Admonition>

## 2. Create a Flag

Create a flag called `show_demo_button` and leave it as Disabled by default:

![Flagsmith Overview](/img/quickstart/demo_create_4.png)

## 3. Use the Flag in Your App

Import the Javascript SDK into your web page:

```html
<script src="https://cdn.jsdelivr.net/npm/flagsmith@latest/index.js"></script>
```

Connect to the Flagsmith API using your Environment API key:

```html {3}
<script>
 flagsmith.init({
  environmentID: '<add your API key here!>',
  onChange: (oldFlags, params) => {
   if (flagsmith.hasFeature('show_demo_button')) {
    var submit_button = document.getElementById('submit_button');
    submit_button.style.display = 'block';
   }
  },
 });
</script>
```

Now, toggling the flag in the Flagsmith dashboard will control the visibility of the button in your app.

<Admonition type="tip" title="Next Steps">
- Explore more about [Feature Flags](./feature-flags.md), [Data Model](./data-model.md), and [Glossary](./glossary.md).
- Check out our [Quick Start Guide](/quickstart) for a broader overview.
</Admonition>


