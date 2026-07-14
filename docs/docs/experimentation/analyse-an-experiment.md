---
title: Analyse an Experiment
sidebar_label: Analyse an Experiment
sidebar_position: 6
description: Read the results page (lift, credible intervals, win probability) and decide when to roll out a winner.
---

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

The experiment's detail page shows who entered the experiment, how each variation performed, and whether you can trust
the numbers.

## Results

Results are computed on demand: click **Refresh results** (at most once every 5 minutes). The **As of** timestamp shows
how fresh the figures are.

The summary scorecards show **Users enrolled**, the current **Winning variation**, its **Chance to be best** and its
**Lift vs control**. See the [Statistics Glossary](/experimentation/statistics) for what each term means.

When a variation reaches a 95% chance of beating control, a recommendation banner suggests rolling it out.

![An experiment page with a winner recommendation banner](/img/experimentation/experiment-results-overview.png)

The analysis table breaks each variation down against control:

- **Exposures**: identities that entered on this variation.
- The metric value (rate, count, sum or mean, depending on the metric).
- **Delta**: how much better or worse the variation did than control, as a percentage.
- **Credible Interval (95%)**: the range the true delta sits in with 95% certainty. If it crosses zero, the result is
  inconclusive.
- **Win Probability**: the chance the variation beats control.

![Results scorecards and the analysis table with credible intervals](/img/experimentation/experiment-results-analysis.png)

While a variation has fewer than 50 identities (or fewer than 5 conversions, for occurrence metrics), it shows
**Collecting data**. Keep the experiment running.

If a **sample ratio mismatch** warning appears, traffic didn't split the way you configured. Don't act on the results.

## Exposures

The **Exposures** panel charts enrolment over time, per variation, with each variation's share of the total.

Identities that were served more than one variation are quarantined and shown as excluded. A small number is normal; a
growing one means users are slipping between variations.

## Ending the experiment

When you have a conclusive result, click **End Experiment**. Results are frozen as final and the flag is unlocked.

To roll out the winner, update the flag so every user gets the winning variation. Once it's permanent, clean up the flag
and remove the losing variations.
