---
id: intro
slug: /
title: Manage feature flags across web, mobile and server side applications
sidebar_position: 1
sidebar_label: Overview
---

# ![Flagsmith Documentation](/img/banner-logo-dark.png)

[Flagsmith](https://flagsmith.com/) lets you manage features across web, mobile and server side applications. Flagsmith
is Open Source. Host yourself or let us take care of the hosting.

The application consist of 3 components:

1. [Server-Side REST API](https://github.com/Flagsmith/flagsmith/tree/main/api).
2. [Front End Administration Web Interface](https://github.com/Flagsmith/flagsmith/tree/main/frontend).
3. [Client Libraries](/#client-libraries).

To get up and running, you can either use [https://flagsmith.com/](https://flagsmith.com/) for 1 and 2 above, or you can
self host the API and Front End. Once you have these components up and running, you can add the client libraries to your
apps and start managing your features remotely.

## Open Source vs SaaS vs Enterprise

You are free to run the Open Source version of Flagsmith however you see fit! There are some differences between the
Open Source, SaaS hosted and Enterprise plans:

- The Open Source version has **no** API request or Identity limits - you can run as many API instances in a cluster as
  you wish
- The Open Source version has **no** Dashboard User limits - you can have as many team members as you wish
- The SaaS and Enterprise versions have [Change Requests and Flag Scheduling](advanced-use/change-requests.md)
- The SaaS and Enterprise versions have [Role-Based Access Controls](advanced-use/permissions.md)
- The SaaS and Enterprise versions have additional [Authentication Providers](enterprise-edition)

## Installation

:::tip

We also have a paid-for [Enterprise Edition](enterprise-edition.md) of the platform with a number of additional
features. Please get in touch if you want to learn more.

:::

More information can be found on the [Self Hosted Page](/deployment/overview).

### Server Side API

The source code and installation instructions can be found at
[the GitHub project](https://github.com/flagsmith/flagsmith). The API is written in Python and is based on Django and
the Django Rest Framework.

### Front End Website

The source code and installation instructions can be found at
[the GitHub project](https://github.com/flagsmith/flagsmith-frontend). The Front End Website is written in
React/Javascript and requires NodeJS.

## Client Libraries

Once you are setup with the front and back end, you can integrate our client libraries within your apps.

| Client Side SDKs                       | Server Side SDKs               |
| -------------------------------------- | ------------------------------ |
| [Javascript](/clients/javascript)      | [Node.js](/v1.0/clients/node)  |
| [Android/Kotlin](/clients/android)     | [Java](/v1.0/clients/java)     |
| [Flutter](/clients/flutter)            | [.Net](/v1.0/clients/dotnet)   |
| [iOS/Swift](/clients/ios)              | [Python](/v1.0/clients/python) |
| [React & React Native](/clients/react) | [Ruby](/v1.0/clients/ruby)     |
| [Next.js and SSR](/clients/next-ssr)   | [Rust](/v1.0/clients/rust)     |
|                                        | [Go](/v1.0/clients/go)         |
|                                        | [Elixir](/v1.0/clients/elixir) |

## What Next

Check out our [Quick Start Guide](quickstart.md) to get a high level overview of how to implement feature flags in your
application.
