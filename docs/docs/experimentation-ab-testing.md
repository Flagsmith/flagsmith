---
title: Experimentation (A/B Testing)
sidebar_label: Experimentation (A/B Testing)
sidebar_position: 4
---

:::info

Experimentation is in active development. Naming, scope, and behaviour
may change before general availability. The draft PR is the place for
feedback.

:::

> **Screenshot placeholder —** Hero image — wide shot of the Experiment Results dashboard with lift bars and the recommendation callout. Target path: `/img/experimentation/hero-results-dashboard.png`

# Experimentation (A/B Testing)

## Overview

Flagsmith Experimentation lets you run controlled A/B tests on your
multivariate feature flags. Metrics are computed from your data
warehouse, and results are read inside Flagsmith.

This guide covers three flows:

- **Connect a data warehouse** — one-time organisation-level setup so
  Flagsmith can compute metric values.
- **Create an experiment** — a 5-step wizard for hypothesis, flag,
  metrics, and audience (targeting, sample size, variation split).
- **Read experiment results** — summary cards, recommendation, metrics
  comparison, and trend chart.

Experimentation builds on three Flagsmith concepts:

- **[Multivariate flags](/managing-flags/core-management).** Every
  experiment runs on one. Existing variations become control and
  treatment.
- **[Segments](/flagsmith-concepts/targeting-and-rollouts).** Optional
  filter on who's eligible for an experiment. Leave empty to run on the
  whole environment.
- **[Identities](/flagsmith-concepts/identities).** Users are bucketed
  by identity, the same way multivariate values are assigned today. A
  user keeps their variation for the duration of the run.

## Prerequisites

A connected data warehouse. See
[Data Warehouse Integration](/third-party-integrations/analytics/data-warehouse)
for setup. The connection is organisation-scoped, so configure it once
per organisation and every project picks it up.

## Creating an experiment

Experiments have their own page in the project sidebar, alongside
Features, Segments, and Identities. Both creating and reading
experiments start here.

![Experiments list page with a mix of Running, Completed, and Draft rows, highlighting the Create Experiment button](/img/experimentation/experiments-list.png)

Click **Create Experiment** in the top right to open the 5-step wizard.
Each step validates before the next; jump back from the Review & Launch
summary at any time.

### Experiment Details

![Experiment Details step — name field, hypothesis textarea, start/end date pickers](/img/experimentation/wizard-details.png)

1. **Name.** A short identifier, e.g. `checkout_paypal_button_test`.
2. **Hypothesis** (required). What you expect to happen, and why. This
   stays attached to the experiment after launch, so the original intent
   is still visible later.
3. **Start and end dates.** Default to today plus 14 days. Change them
   to schedule for later or run a longer window.

### Flag & Variations

![Flag picker with multi-variant flags; the single-variant blocking banner below for context](/img/experimentation/wizard-flag-variations.png)

Pick the **multivariate flag** to experiment on. The Variations table
shows the flag's existing values, which become the experiment's control
and treatment.

Single-variant flags aren't eligible. The wizard blocks them and links
to the flag's page so you can add a variation.

**Note:** Experiments need at least one non-control variation. If the
flag doesn't have one, the wizard points you to the flag's main page to
add it.

### Select Metrics

![Metric picker showing pre-selected metrics with the Primary / Secondary / Guardrail segmented control visible on a row](/img/experimentation/wizard-metrics.png)

Select the metrics this experiment will track. Each metric has a role:

- **Primary.** Drives the verdict. The experiment succeeds or fails
  based on significance here.
- **Secondary.** Tracked alongside primary metrics, but doesn't
  influence the recommendation.
- **Guardrail.** A safety check for metrics you don't want to break,
  such as page-load time or error rate.

Pick a role for each metric with the three-way segmented control.
Multiple primaries are allowed but harder to interpret statistically;
the wizard warns you if you select more than one.

### Audience

![Audience step with three sub-blocks: Targeting, Sample size, Variation split](/img/experimentation/wizard-audience.png)

The audience step has three layers, applied in order:

1. **Targeting** — *who's eligible.*
2. **Sample size** — *of those, how many enter the experiment.*
3. **Variation split** — *of those sampled, who sees what.*

Each layer is independent, which lets you run a 10% canary on the whole
environment, a 50/50 test on premium users only, or anything in between.

#### Targeting (optional)

Filter the experiment to a specific segment. Leave empty to run on all
identities in the environment, which is the default. Users not matched
by the segment keep the flag's environment default and aren't part of
the result.

:::warning

If the flag already has an override for the chosen segment, the wizard
blocks you with a conflict banner. Pick a different segment or remove
the override before continuing. A live experiment on a segment with an
override produces incorrect assignment.

:::

#### Sample size

Choose what percentage of eligible users actually enters the
experiment. Presets are 5 / 10 / 25 / 50 / 100, or pick Custom for any
value. Defaults to 100. Eligible users not sampled in keep the flag's
environment default — they're not part of the result.

Use a smaller sample to start a canary and validate before ramping
wider. Use 100 when you want every eligible user in the result from
day one.

#### Variation split

Distribute the sampled users across control and treatment variations.
Control takes one of the weight slots alongside the variations, so a
50/50 split means 50% control, 50% treatment. Weights auto-balance, so
adjusting one rebalances the others. Click **Split evenly** to reset.

**Note:** In v1, only one experiment can run on a given segment + flag
at a time. Changing the variation split mid-run breaks statistical
validity, so design with the final split up front. To ramp the
audience size, use the sample-size dial — it changes who's in the
experiment without changing how the in-experiment users are split.

### Review & Launch

![Review summary with per-section edit links](/img/experimentation/wizard-review-launch.png)

Read through the summary, edit any section by clicking its **Edit**
link, then click **Launch Experiment** and confirm.

Traffic assignment starts immediately. The flag begins serving the
configured variation weights to the sampled portion of the eligible
audience; everyone else keeps the flag's environment default.

**Note:** Once launched, the configuration is locked for the rest of
the run to keep the result statistically valid. To change anything,
stop the experiment and start a new one.

## Reading experiment results

Click any running or completed experiment from the **Experiments** list
to open its **Results** dashboard.

![Full results dashboard — stat cards, recommendation callout, metrics comparison table, and trend chart stacked](/img/experimentation/results-dashboard-full.png)

### Summary cards

- **Lift vs. control** on the primary metric.
- **Probability of being best.** Confidence that the leading variation
  actually wins.
- **Sample size per variation.** How many assigned identities have
  contributed data so far.

### Recommendation callout

![Recommendation callout — "Treatment B is outperforming Control with 94% probability" style](/img/experimentation/results-recommendation-callout.png)

A plain-language summary: which variation is leading, how confident the
verdict is, and what to do next (keep running, declare a winner, or
investigate).

### Metrics comparison table

![Metrics comparison table — primary row emphasised, guardrail badge visible, zero-centred lift bars](/img/experimentation/results-comparison-table.png)

One row per metric, with the primary row visually emphasised. Each row
shows:

- **Role badge.** Primary, Secondary, or Guardrail.
- **Control value** and **Treatment value.**
- **Lift bar.** Zero-centred, showing the relative change and its
  direction.
- **Significance.** Statistical confidence in the observed lift.

### Trend over time

![Trend line chart with metric selector above it — control vs. treatment lines](/img/experimentation/results-trend-chart.png)

A line chart plots each variation's value over the experiment's run.
Use the metric selector above the chart to switch between metrics.

Look for stability. Lines separated for several days are more
trustworthy than ones that crossed yesterday.

## What's next

- **[Multivariate flags](/managing-flags/core-management).** The
  building block under every experiment.
- **[Segments](/flagsmith-concepts/targeting-and-rollouts).** Define
  an experiment's audience.
- **[Identities](/flagsmith-concepts/identities).** The unit Flagsmith
  buckets users by.
