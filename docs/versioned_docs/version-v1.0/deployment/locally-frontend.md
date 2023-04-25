---
sidebar_label: Frontend
title: Flagsmith Frontend
sidebar_position: 20
---

## Getting Started

These instructions will get you a copy of the project front end up and running on your local machine for development and
testing purposes. See running in production for notes on how to deploy the project on a live system.

## Prerequisites

What things you need to install the software and how to install them

| Location                                    | Suggested Version |
| ------------------------------------------- | :---------------: |
| <a href="https://nodejs.org/en/">NodeJS</a> |     >= 16.0.0     |
| <a href="https://nodejs.org/en/">npm</a>    |     >= 8.0.0      |

## Installing

```bash
cd frontend
npm i
```

## Running the Front End

### Development

Hot reloading for client / server

```bash
cd frontend
npm run dev
```

### Production

You can deploy this application on [Heroku](https://www.heroku.com/) and [Dokku](http://dokku.viewdocs.io/dokku/)
without making any changes, other than the API URL in '/frontend/env/project_prod.js'

Bundles, minifies and cache busts the project to a build folder and runs node in production. This can be used as part of
your deployment script.

```bash
cd frontend
npm run bundle
npm start
```

## Environment Variables

Variables that differ per environment are exported globally to `window.Project in` 'frontend/common/project.js', this
file gets replaced by a project.js located in 'frontend/env' by webpack based on what is set to the "ENV" environment
variable (e.g. ENV=prod).

You can override each variable individually or add more by editing 'frontend/bin/env.js'.

Current variables used between 'frontend/environment.js' and 'frontend/common/project.js':

- `FLAGSMITH_API_URL`: The API to hit for requests. E.g. `https://api.flagsmith.com/api/v1/`
- `FLAGSMITH_ON_FLAGSMITH_API_KEY`: The flagsmith environment key we use to manage features -
  [Flagsmith runs on Flagsmith](/deployment/overview#running-flagsmith-on-flagsmith).
- `FLAGSMITH_ON_FLAGSMITH_API_URL`: The API URL which the flagsmith client should communicate with. Flagsmith runs on
  flagsmith. E.g. `https://api.flagsmith.com/api/v1/`. If you are self hosting and using your own Flagsmith instance to
  manage its own features, you would generally point this to the same domain name as your own Flagsmith instance.
- `ENABLE_INFLUXDB_FEATURES`: Enables any features that rely on influxdb. API Usage charts, flag analytics. E.g.
  `ENABLE_INFLUXDB_FEATURES=1`.
- `ENABLE_FLAG_EVALUATION_ANALYTICS`: Determines if the flagsmith sdk should send usage analytics, if you want to enable
  Flag Analytics, set this. E.g. `ENABLE_FLAG_EVALUATION_ANALYTICS=1`.
- `PROXY_API_URL`: Proxies the API via this application. Set this to the hostname of the API being proxied. Proxies
  `/api/v1/` through to `PROXY_API_URL`. If you are using this, any setting to `FLAGSMITH_API_URL` will be ignored and
  the browser will use the front end node server to send API requests. Do not prepend `api/v1/` - it will be added
  automatically.
- `GOOGLE_ANALYTICS_API_KEY`: Google Analytics key to track API usage.
- `CRISP_WEBSITE_ID`: Crisp Chat widget Website key.
- `ALLOW_SIGNUPS`: **DEPRECATED in favour of PREVENT_SIGNUP** Determines whether to prevent manual signups without
  invites. Set it to any value to allow signups.
- `PREVENT_SIGNUP`: Determines whether to prevent manual signups without invites. Set it to any value to prevent
  signups.
- `PREVENT_FORGOT_PASSWORD`: Determines whether to prevent forgot password functionality, useful for LDAP/SAML. Set it
  to any value to prevent forgot password functionality.
- `ENABLE_MAINTENANCE_MODE`: Puts the site into maintenance mode. Set it to any value to enable maintenance.
- `AMPLITUDE_API_KEY`: The Amplitude key to use for behaviour tracking.
- `MIXPANEL_API_KEY`: Mixpanel analytics key to use for behaviour tracking.
- `SENTRY_API_KEY`: Sentry key for error reporting.
- `STATIC_ASSET_CDN_URL`: Used for replacing local static paths with a cdn, .e.g https://cdn.flagsmith.com. Defaults to
  `/`, i.e. no CDN.
- `BASE_URL`: Used for specifying a base url path that's ignored during routing if serving from a subdirectory

## E2E testing

This project uses [Test Cafe](https://testcafe.io/) for automated end to end testing with Chromedriver.

```bash
npm test
```

## Built With

- React
- Webpack
- Node

## Running locally against your own Flagsmith API instance

We use Flagsmith to manage features we rollout, if you are using your own Flagsmith environment (i.e. by editing
project_x.js-> flagsmith) then you will need to have a replica of our flags.

A list of the flags and remote config we're currently using in production can be
[found here](/deployment/overview#current-flagsmith-feature-flags).
