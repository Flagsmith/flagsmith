# Flagsmith Frontend

The frontend application for [https://flagsmith.com/](https://www.flagsmith.com/). Flagsmith allows you to manage feature flags and remote config across multiple projects, environments and organisations.

This project connects to the [Flagsmith API](https://github.com/Flagsmith/Bullet-Train-API).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See running in production for notes on how to deploy the project on a live system.

## Prerequisites

What things you need to install the software and how to install them

| Location                                                     | Suggested Version       |
| -------------                                                |:-------------:|
| <a href="https://nodejs.org/en/">NodeJS</a>                     | >= 6.0.0 |
| <a href="https://nodejs.org/en/">npm</a>                        | >= 4.0.0 |

## Installing

```bash
npm i
```

## Running

**Development**

Hot reloading for client / server

```bash
npm run dev
```

**Production**

You can deploy this application on [Heroku](https://www.heroku.com/) and [Dokku](http://dokku.viewdocs.io/dokku/) without making any changes, other than the API URL in [project_prod.js](/env/project_prod.js)  

Bundles, minifies and cache busts the project to a build folder and runs node in production. This can be used as part of your deployment script.

```bash
npm run bundle
npm start
```

## ENV variables

Variables that differ per environment are exported globally to ``window.Project in`` [common/project.js](./common/project.js), this file gets replaced by a project.js located in [env](./env) by webpack based on what is set to the "ENV" environment variable (e.g. ENV=prod).

You can override each variable individually or add more by editing [./bin/env.js](./bin/env.js). 

Current variables used between [environment.js](./bin/env.js) and [common/project.js](./bin/env.js):

- API_URL: The API to hit for requests. E.g. `https://api.flagsmith.com/api/v1/`
- FLAGSMITH: The flagsmith environment key we use to manage features - Flagsmith runs on Flagsmith.
- FLAGSMITH_CLIENT_API: The api which the flagsmith client should communicate with. Flagsmith runs on flagsmith. E.g. `https://api.flagsmith.com/api/v1/`.
- DISABLE_INFLUXDB_FEATURES: Disables any features that rely on influxdb. API Usage charts, flag analytics. E.g. `DISABLE_INFLUXDB_FEATURES=1`.
- FLAGSMITH_ANALYTICS: Determines if the fagsmith sdk should send usage analytics, if you want to disable analytics don't set this. E.g. `true`.
- PROXY_API_URL: Proxies the API via this application. Set this to the hostname of the API being proxied. Proxies `/api/v1/` through to `PROXY_API_URL`. If you are using this, any setting to `API_URL` will be ignored and the browser will use the front end node server to send API requests. Do not prepend `api/v1/` - it will be added automatically.
- GA: Google analytics key
- CRISP_CHAT: Crisp Chat widget key
- PREVENT_SIGNUP: Determines whether to prevent manual signup without invite. Set it to any value to disable signups.
- MAINTENANCE: Puts the site into maintenance mode. Set it to any value to disable signups.
- AMPLITUDE: The ampitude key to use for behaviour tracking.
- MIXPANEL: Mixpanel analytics key to use for behaviour tracking.
- SENTRY: Sentry key for error reporting.
- ASSET_URL: Used for replacing local static paths with a cdn, .e.g https://cdn.flagsmith.com. Defaults to `/`, i.e. no CDN.
- BASENAME: Used for specifying a base url path that's ignored during routing if serving from a subdirectory

## E2E testing

This project uses [Nightwatch](http://nightwatchjs.org/) for automated end to end testing with chromedriver.

```bash
npm test
```

## Built With

- React
- Webpack
- Node

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/kyle-ssg/c36a03aebe492e45cbd3eefb21cb0486) for details on our code of conduct, and the process for submitting pull requests to us.

## Getting Help

If you encounter a bug or feature request we would like to hear about it. Before you submit an issue please search existing issues in order to prevent duplicates.

## Get in touch

If you have any questions about our projects you can email <a href="mailto:projects@solidstategroup.com">projects@solidstategroup.com</a>.

## Running locally against your own Flagsmith API instance

We use Flagsmith to manage features we rollout, if you are using your own Flagsmith environment (i.e. by editing project_x.js-> flagsmith) then you will need to have a replica of our flags.

A list of the flags and remote config we're currently using in production can be found here https://gist.github.com/kyle-ssg/55f3b869c28bdd13c02c6688bc76c67f.

## Useful links

[Website](https://flagsmith.com)

[Product Roadmap](https://github.com/Flagsmith/flagsmith/projects/1)

[Documentation](https://docs.flagsmith.com/)

[Code Examples](https://github.com/Flagsmith/bullet-train-docs)

[Youtube Tutorials](https://www.youtube.com/channel/UCki7GZrOdZZcsV9rAIRchCw)
