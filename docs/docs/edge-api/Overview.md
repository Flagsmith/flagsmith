---
id: overview
title: Edge API Overview
sidebar_position: 1
sidebar_label: Overview
---

## Authentication

The Edge API is designed to be publicly accessible. Calls need to have an environment key supplied with each request.
This is provided as an HTTP header, with the name `X-Environment-Key` and the value of the Environment Key that you can
find within the Flagsmith administrative area.

## Core API

Please note that the Edge API is specifically to be used with our [SDKs](/clients). If you want to drive aspects of
Flagsmith programmatically, you need to use our private [Core API](/clients/rest#private-admin-api-endpoints).

You can find the full spec to our Core API [here](https://api.flagsmith.com/api/v1/docs/).
