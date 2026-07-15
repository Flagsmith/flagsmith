---
title: Create Metrics
sidebar_label: Create Metrics
sidebar_position: 3
description: Define the outcomes your experiments measure, computed from the events your application sends.
---

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

A metric defines an outcome you measure, computed from the events your application sends to the warehouse. Metrics are
defined per environment and can be reused across experiments.

To create one, go to the **Metrics** page and click **Create Metric**, or click **Create Metric** in the experiment
wizard's Measurement step.

<!-- Screenshot: Create Metric form -->

## Fields

**Name** and an optional description, e.g. "Signup Completion Rate".

**What do you want to measure?** sets how the metric aggregates events, per identity:

| Aggregation    | What it measures                         | Example             |
| -------------- | ---------------------------------------- | ------------------- |
| **Occurrence** | Whether an event is seen at least once   | Signup completion   |
| **Count**      | Number of times an event occurred        | Number of purchases |
| **Sum**        | Total of a numeric value across events   | Total revenue       |
| **Mean**       | Average of a numeric value across events | Average order value |

:::important

Sum and Mean aggregate the numeric `value` sent with each event, so your application must include it:

```javascript
flagsmith.trackEvent('purchase', { value: 99.5 });
```

:::

**Direction** sets whether higher is better, lower is better, or the metric is informational only. This is the metric's
inherent polarity; it pre-fills the **expected direction** you choose when attaching the metric to an experiment.

**Event name** is the event this metric aggregates, e.g. `checkout_completed`. It must exactly match the event name your
application sends (see [Run an Experiment](/experimentation/run-an-experiment)).

A metric attached to an active experiment cannot be deleted.
