---
title: Create an Experiment
sidebar_label: Create an Experiment
sidebar_position: 4
description: Set up an experiment on a multivariate flag. Name it, configure the rollout, and pick a primary metric.
---

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

An experiment serves the variations of a [multivariate flag](/managing-flags/core-management) to a share of your users
and measures the impact on a metric.

## 0. Pre-requisites

- A [connected warehouse](/experimentation/connect-a-warehouse).
- A [**multivariate flag**](/managing-flags/core-management) with a variation for each treatment you want to test. The
  flag's current value acts as the **control**. A flag can only be in one active experiment at a time.
- A [metric](/experimentation/create-metrics). You can also create one from inside the wizard.

On the **Experiments** page, click **Create Experiment**. The wizard has four steps.

## 1. Setup

Give the experiment a name and a hypothesis, and select the flag to experiment on. A good hypothesis names the change,
the metric, the expected magnitude and the timeframe. For example: _"Redesigning the checkout button with a clearer CTA
will increase conversion rates by at least 15% within 30 days."_

![The Setup step: experiment name, hypothesis and feature flag](/img/experimentation/create-experiment-setup.png)

## 2. Rollout configuration

Two settings control who sees what:

- **Rollout**: the percentage of identities that enter the experiment at all. Identities outside the rollout keep the
  flag's normal behaviour and are not counted in the results.
- **Variation split**: how identities _inside_ the rollout are distributed across control and the variations. Weights
  must sum to 100, and control takes whatever the variations don't. Use **Split evenly** for an equal distribution.

For example, with a rollout of 20% and a 50/50 split, 10% of your identities see the control, 10% see the variation, and
the remaining 80% are untouched.

Bucketing is deterministic on the identity key, so the same identity always lands in the same variation.

![The Rollout configuration step: rollout percentage, variation split and distribution bar](/img/experimentation/create-experiment-rollout.png)

## 3. Measurement

Select the **primary metric** (the metric the experiment is judged on) and set the **expected direction**: increase,
decrease, should not increase, or should not decrease. If the metric doesn't exist yet, click **Create Metric**.

## 4. Review & Launch

Review the configuration and click **Create Experiment**. The experiment starts immediately.

:::caution

While an experiment is running, its flag configuration and variations are locked. The rollout percentage can still be
edited from the experiment page.

:::

A running experiment can be **ended** at any time. Once ended, the results are frozen as final and the experiment cannot
be restarted — you would need to create a new one.
