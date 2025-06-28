---
title: Create Your First Flag
description: "A hands-on tutorial to create and use your first feature flag in Flagsmith."
sidebar_position: 1
---
import Admonition from '@theme/Admonition';

# Create Your First Flag

Feature flags (also called feature toggles) let you enable or disable features remotely, without deploying new code. In this tutorial, you'll learn how to create a feature flag in Flagsmith and use it to control a feature in your application, step by step, using the Flagsmith dashboard and a simple web page.


<Admonition type="info" title="Before you begin">
* Sign up for a [Flagsmith account](https://app.flagsmith.com/signup).<br />
* Have a simple HTML/JS project or web page ready to test the flag.
</Admonition>

# Steps

1. **Create an Organisation**  
   After signing up, create your first Organisation in the Flagsmith dashboard.
   
   ![Create Organisation](/img/quickstart/demo_create_1.png)

2. **Create a Project**  
   Next, create a Project within your Organisation. Projects help you group related features and environments (like Development and Production).
   
   ![Create Project](/img/quickstart/demo_create_2.png)

3. **Create a Flag**  
   In your Project, create a flag called `show_demo_button` and leave it Disabled by default.
   
   ![Flagsmith Overview](/img/quickstart/demo_create_4.png)

4. **Integrate the Flag in Your App**  
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

# Summary
- You created a feature flag in Flagsmith.
- You connected your app to Flagsmith and used the flag to control a UI element.

# Next steps
- Learn more about [Feature Flags](./feature-flags.md) and [Data Model](./data-model.md)
- Explore [Flag Management](/advanced-use/flag-management) and [Best Practices](https://www.flagsmith.com/blog/feature-flags-best-practices?utm_source=app)
- See the [Glossary](./glossary.md) for key terms


