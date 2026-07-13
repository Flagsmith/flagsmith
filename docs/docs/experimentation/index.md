---
title: Experimentation
description:
 'Run A/B tests natively in Flagsmith: serve variations, collect events, and analyse results with built-in Bayesian
 statistics.'
---

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

Flagsmith Experimentation lets you run A/B tests end to end on the platform: serve variations of a feature with a
[multivariate flag](/managing-flags/core-management), collect events from your application into a managed data
warehouse, and read the results with a built-in Bayesian statistics engine.

Experiments are scoped to an **environment**: the warehouse connection, metrics and experiments all live at the
environment level.

## Set up and run an experiment

1. **[Connect a warehouse](/experimentation/connect-a-warehouse)**: enable the managed Flagsmith warehouse for your
   environment. Done once, in a few clicks.
2. **[Create metrics](/experimentation/create-metrics)**: define the outcomes you measure, computed from the events your
   application sends.
3. **[Create an experiment](/experimentation/create-an-experiment)**: pick a multivariate flag, decide how much traffic
   enters the test and how it is split, and choose a primary metric.
4. **[Run the experiment](/experimentation/run-an-experiment)**: instrument your application to record exposures and
   conversion events with the Flagsmith SDKs.
5. **[Analyse the results](/experimentation/analyse-an-experiment)**: read lift, credible intervals and win probability
   on the experiment's results page, then roll out the winner.

Prefer to see it end to end? Follow the [PayPal button example](/experimentation/example-paypal-button).

Unfamiliar with a term? The [Statistics Glossary](/experimentation/statistics) explains every concept in plain language.

## A/B testing without the Experimentation feature

You can also run A/B tests with multivariate flags and your own analytics platform. See
[Experimentation (A/B Testing)](/experimentation-ab-testing).
