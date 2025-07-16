---
title: Feature Flags
sidebar_label: Feature Flags
sidebar_position: 1
---

Feature Flags are a development methodology that allow you to ship code and features in your application before they are finished. A feature flag is a control point in your code that determines whether a particular feature or behaviour is active. Flags can be simple on/off (boolean) switches, or multivariate, allowing you to select from multiple options or variants.

### What do Feature Flags enable?

- **Decouple deployment from release:** Ship code to production with features hidden behind flags, then enable them for users when ready.

- **Staged rollouts:** Gradually enable features for a subset of users, reducing risk and allowing for real-world testing. [Learn more](/guides-and-examples/staged-feature-rollouts.md)

- **A/B testing and experimentation:** Test multiple variants of a feature and measure impact. [Learn more](/advanced-use/ab-testing.md)

- **Remote configuration:** Change app behaviour or configuration in real time, without redeploying.

### Advantages of using Feature Flags

- **Safer releases:** Reduce the risk of deploying new features by controlling exposure.
- **Faster iteration:** Test and iterate on features quickly, without waiting for deployment cycles.
- **Targeted rollouts:** Enable features for specific users, groups, or environments.
- **Easy rollback:** Instantly turn off features if bugs or issues are detected.
- **Experimentation:** Run experiments and gather data to inform product decisions.

### Workflow

1. You are about to start work on a new feature. Let's imagine you are going to implement a sharing button with your application.

2. Create a new Feature Flag in Flagsmith, calling it "sharing_button". Set it to enabled on your development environment, and disabled on your production environment.

3. Start working on the feature. Whenever you write code that shows the button within the UI, wrap it in a conditional statement, testing against the value of the flag "sharing button". Only show the button if the flag is set to True.

4. Because your button only shows when the "sharing_button" flag is set to True, you are safe to commit your code as you work on the feature. Your code will be live within the production platform, but the functionality is hidden behind the flag.

5. Once you are happy with your Feature, you can enable the "sharing_button" for other members of your team and with beta testers.

6. If everything is working as intended, switch the "sharing_button" flag to True for everyone in your production environment, and your feature is rolled out.

If you want to learn more about Feature Flags,
[Flickr wrote the seminal blog post on it in 2009](https://code.flickr.net/2009/12/02/flipping-out/).
