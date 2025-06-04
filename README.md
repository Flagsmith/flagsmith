[![Feature Flag, Remote Config and A/B Testing platform, Flagsmith](static-files/hero.png)](https://www.flagsmith.com/)

[![Stars](https://img.shields.io/github/stars/flagsmith/flagsmith)](https://github.com/Flagsmith/flagsmith/stargazers)
[![Docker Pulls](https://img.shields.io/docker/pulls/flagsmith/flagsmith)](https://hub.docker.com/u/flagsmith)
[![Docker Image Size](https://img.shields.io/docker/image-size/flagsmith/flagsmith)](https://hub.docker.com/r/flagsmith/flagsmith)
[![Join the Discord chat](https://img.shields.io/discord/517647859495993347)](https://discord.gg/hFhxNtXzgm)
[![Coverage](https://codecov.io/gh/Flagsmith/flagsmith/branch/main/graph/badge.svg?token=IyGii7VSdc)](https://codecov.io/gh/Flagsmith/flagsmith)
<a href="https://depot.dev?utm_source=Flagsmith"><img src="https://depot.dev/badges/built-with-depot.svg" alt="Built with Depot" height="20"></a>

[Flagsmith](https://flagsmith.com/) is an open source, fully featured, Feature Flag and Remote Config service. Use our
hosted API, deploy to your own private cloud, or run on-premise.

# Flagsmith

Flagsmith makes it easy to create and manage features flags across web, mobile, and server side applications. Just wrap
a section of code with a flag, and then use Flagsmith to toggle that feature on or off for different environments, users
or user segments.

Get up and running in less than a minute:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
docker-compose -f docker-compose.yml up
```

The application will bootstrap an admin user, organisation, and project for you. You'll find a link to set your password
in your Compose logs:

```txt
Superuser "admin@example.com" created successfully.
Please go to the following page and choose a password: http://localhost:8000/password-reset/confirm/.../...
```

Note: This setup uses http:// for local development. If you've configured SSL for your local environment, you may use
https:// instead. For any production deployment, always use https://.

![Flagsmith Screenshot](static-files/screenshot.png)

## Features

- **Feature flags**. Release features with confidence through phased roll-outs.
- **Remote config**. Easily toggle individual features on and off, and make changes without deploying new code.
- **A/B and Multivariate Testing**. Use segments to run A/B and multivariate tests on new features. With segments, you
  can also introduce beta programs to get early user feedback.
- **Organization Management**. Organizations, projects, and roles for team members help keep your deployment organized.
- **Integrations**. Easily enhance Flagsmith with your favourite tools.

## Trying Flagsmith

### Flagsmith hosted SaaS

You can try our hosted version for free at https://flagsmith.com/

### Flagsmith Open Source

The Flagsmith API is built using Python 3, Django 4, and DjangoRestFramework 3. You can try the application out using:

- [Docker](https://github.com/Flagsmith/flagsmith/blob/main/docker-compose.yml)
- [Kubernetes](https://github.com/Flagsmith/flagsmith-charts)
- [Redhat OpenShift](https://operatorhub.io/operator/flagsmith)

We also have options for deploying to AWS, GCP, Azure and On-Premise. If you need help getting up and running, please
[get in touch!](mailto:support@flagsmith.com)

## Overview

This repository is formed of 2 core components, the REST API (found in `/api`) and the web-based administrator dashboard
(found in `/frontend`) that you can use to manage Flagsmith. Technical documentation for each component can be found at
the [API](https://docs.flagsmith.com/deployment/locally-api) and
[Frontend](https://docs.flagsmith.com/deployment/locally-frontend) pages within our
[Documentation](https://docs.flagsmith.com/)

These two components run as separate applications. The web-based dashboard is a single page app that communicates via
REST calls to the API.

## Resources

- [Website](https://flagsmith.com/)
- [Documentation](https://docs.flagsmith.com/)
- If you have any questions about our projects you can email [support@flagsmith.com](mailto:support@flagsmith.com)

