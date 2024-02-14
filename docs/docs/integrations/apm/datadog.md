---
title: Datadog Integration
sidebar_label: Datadog
hide_title: true
---

import ReactPlayer from 'react-player'

![Datadog](/img/integrations/datadog/datadog-logo.svg)

You can integrate Flagsmith with Datadog in three ways:

- [1. Integrate Flagsmith into your Datadog Dashboard](#1-integrate-flagsmith-into-your-datadog-dashboard)
- [2. Send Flag Change events to Datadog](#2-send-flag-change-events-to-datadog)
- [3. Integrate with the DataDog RUM](#3-integrate-with-the-datadog-rum)

## 1. Integrate Flagsmith into your Datadog Dashboard

This integration lets you add a Flagsmith widget into your Datadog Dashboard so you can view and manage your flags
without having to leave the Datadog application.

![Datadog Dashboard Widget](/img/integrations/datadog/datadog-dashboard-widget.png)

The video below will walk you through the steps of adding the integration:

<ReactPlayer
    playing
    controls
    width="100%"
    height="460px"
    url='https://getleda.wistia.com/medias/76558s9yj7' />

## 2. Send Flag Change events to Datadog

The second type of integration allows you to send Flag change events in Flagsmith into your Datadog event stream.

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

## 3. Integrate with the DataDog RUM

You can also send Identity flag values from Flagsmith to DataDog using our
[Javascript Integration](/clients/client-side/javascript.md#datadog-rum-javascript-sdk-integration).
