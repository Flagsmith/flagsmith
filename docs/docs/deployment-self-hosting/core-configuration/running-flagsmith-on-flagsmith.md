---
title: "Running Flagsmith on Flagsmith"
description: "How to configure a self-hosted instance to use its own flags for feature management."
sidebar_position: 50
---

Flagsmith uses Flagsmith to control features on the frontend dashboard. If you are self-hosting the platform, you will sometimes see features greyed out, or you may want to disable specific features, e.g. logging in via Google and GitHub. If you are using your own Flagsmith environment, then you will need to have a replica of our flags in order to control access to those features.

## Setup Process

To do this, first create a new project within your self-hosted Flagsmith application. This is the project that we will use to control the features of the self-hosted Flagsmith instance. We will then point the self-hosted frontend dashboard at this Flagsmith project in order to control what features show for your self-hosted Flagsmith instance.

## Environment Variables

Once you have created the project, you need to set the following [Frontend](https://github.com/Flagsmith/flagsmith-frontend) environment variables in order to configure this:

- `FLAGSMITH_ON_FLAGSMITH_API_KEY`
  - The Flagsmith Client-side Environment Key we use to manage features - Flagsmith runs on Flagsmith. This will be the API key for the project you created as instructed above.
- `ENABLE_FLAGSMITH_REALTIME`
  - Determines whether the Flagsmith on Flagsmith SDK uses Realtime.
- `FLAGSMITH_ON_FLAGSMITH_API_URL`
  - The API URL which the Flagsmith frontend dashboard should communicate with. This will most likely be the domain name of the Flagsmith API you are self-hosting: Flagsmith runs on Flagsmith. E.g. For our SaaS hosted platform, the variable is `https://edge.api.flagsmith.com/api/v1/`. For example, if you were running everything locally using the standard [docker-compose setup](https://github.com/Flagsmith/flagsmith-docker), you would use `http://localhost:8000/api/v1/`

## Verification and Usage

Once you have set this up, you should see the Flagsmith frontend requesting its own flags from the API (you can look in your browser developer console to see this). You can now start creating flags and overriding the default behaviours of the platform. For example, if you wanted to disable Google OAuth authentication, you would create a flag called `oauth_google` and disable it. 