---
title: Feature Flags
sidebar_label: Feature Flags
sidebar_position: 1
---

Feature Flags are a development methodology that allow you to ship code and features before they are finished. This greatly benefits Continuous Integration and Continuous Deployment (CI/CD). The typical workflow for this is as follows.

1. You are about to start work on a new feature. Lets imaging you are going to implement a sharing button with your application.

2. Create a new Feature Flag in Flagsmith, calling it "sharing_button". Set it to enabled on your development environment, and disabled on your production environment.

3. Start working on the feature. Whenever you write code that shows the button within the UI, wrap it in a conditional statement, testing against the value of the flag "sharing button". Only show the button if the flag is set to True.

4. Because your button only shows when the "sharing_button" flag is set to True, you are safe to commit your code as you work on the feature. Your code will be live within the production platform, but the functionality is hidden behind the flag.

5. Once you are happy with your Feature, you can enable the "sharing_button" for other members of your team and with Beta testers.

6. If everything is working as intended, flip the "sharing_button" flag to True for everyone in your production environment, and your feature is rolled out.

If you want to learn more about Feature Flags,
[Flickr wrote the seminal blog post on it in 2009](https://code.flickr.net/2009/12/02/flipping-out/).
