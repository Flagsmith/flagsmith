---
title: Datadog Integration
sidebar_label: Datadog
hide_title: true
---

import ReactPlayer from 'react-player'

![Datadog](/img/integrations/datadog/datadog-logo.svg)

You can integrate Flagsmith with Datadog in two ways:

- [1. Send flag change events to Datadog](#1-send-flag-change-events-to-datadog)
  - [Custom Source](#custom-source)
- [2. Integrate with the Datadog RUM](#2-integrate-with-the-datadog-rum)

## 1. Send Flag Change events to Datadog

The second type of integration allows you to send flag change events in Flagsmith into your Datadog event stream.

![Datadog](/img/integrations/datadog/datadog-3.png)

1. Log into Datadog and go to Organization Settings > Access > API
2. Generate a new API key
3. Add the Datadog API key into Flagsmith (Integrations > Add Datadog Integration)
4. Add the Datadog URL into Flagsmith as the Base URL - (This is either `https://api.datadoghq.com/` or
   `https://api.datadoghq.eu/`)

### Custom Source

By checking the 'Use Custom Source' option, we will send all events with the source 'Flagsmith'. Leaving this unchecked
will mean events are labelled with the default 'My apps' source.

Flag change events will now be sent to Datadog.

## 2. Integrate with the DataDog RUM

You can also send identity flag values from Flagsmith to Datadog using our
[Javascript Integration](/integrating-with-flagsmith/sdks/client-side-sdks/javascript#datadog-rum-javascript-sdk-integration). 