---
title: AppDynamics Integration
sidebar_label: AppDynamics
hide_title: true
---

![Amplitude](/img/integrations/appdynamics/appdynamics-logo.svg)

You can integrate Flagsmith with AppDynamics. This integration is helpful if you are self hosting and wanting to analyse
the performance of Flagsmith in more detail.

:::note

AppDynamics is an Enterprise-only integration.

:::

## Setup

The application supports the use of AppDynamics for monitoring purposes. In order to setup AppDynamics for your
environment follow the steps below:

1. Set up your application in your AppDynamics dashboard using the "Getting Started Wizard - Python".
2. In the wizard you will need to select the "uWSGI with Emperor: Module Directive" when choosing a deployment method
3. On completing the wizard you will be provided with a configuration file named something like
   `appdynamics.template.cfg` provided, except with your application information. Make a copy of this information a
   place it in a file at the root of this repository called `appdynamics.cfg`. _Note_: there is a bug in the AppDynamics
   wizard that sets the value `ssl = (on)` which needs to be changed to `ssl = on`

## Running with docker-compose

When running with the `docker-compose.yml` file provided ensure the `APP_DYNAMICS` argument is set to `on` as seen
below:

```yaml
api:
 build:
 context: .
 dockerfile: docker/Dockerfile
 args:
  APP_DYNAMICS: 'on'
```

Running the command below will build the docker image with all the AppDynamics config included

```bash
docker-compose -f docker-compose.yml build
```

This image can then be run locally using the docker-compose `up` command as seen below

```bash
docker-compose -f docker-compose.yml up
```

## Additional Settings

If you need additional AppDynamics setup options you can find the other environment variables you can set
[here](https://docs.appdynamics.com/display/PRO21/Python+Agent+Settings).
