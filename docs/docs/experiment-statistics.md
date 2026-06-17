---
title: Experiment Statistics
sidebar_label: Experiment Statistics
sidebar_position: 5
---

Flagsmith's statistics engine answers three questions about an experiment: **Am I winning?** (is the variant better than
control), **by how much?** (the lift), and **can I trust it?** (is the difference real, and was traffic split fairly).
This page explains the terms you'll see, in plain language — no statistics background needed.

:::info Coming soon — Enterprise beta

Experiment statistics aren't generally available yet. They are launching as a beta on **Enterprise** plans — to join,
[get in touch](https://www.flagsmith.com/contact-us). Everything described on this page is part of that upcoming
release; it previews what the feature will do.

:::

## Terms you'll see

**Experiment** — A controlled comparison: show different versions of a feature to different people, measure which
performs better.

**Variant** — One version being compared. Each person sees exactly one.

**Control** — The "leave things as they are" variant — your current experience, the baseline everything is measured
against (its key is the reserved value `control`).

**Treatment** — Any variant that isn't the control — the change you're testing.

**Identity** — One user, device, or account — the individual whose behaviour you measure.

**Exposure** — The moment an identity is shown a variant. The exposure count is how many people entered the experiment.

**Conversion rate** — The percentage of people who did the thing you care about (4.21% ≈ 4 in 100).

**Metric** — What you measure to judge success — checkout rate, revenue, page views.

**Goal metric** — A metric you want to improve (the reason you're running the experiment).

**Guardrail metric** — A metric you want to keep an eye on so the change doesn't make it worse.

**Lift** — How much better or worse a variant did than control, as a percentage. "+11%" means 11% better.

**Credible interval** — Our confidence range — the band we're 95% sure the true lift falls inside. Narrow = precise;
wide = needs more data.

**Chance to beat control (chance to win)** — The probability a variant is genuinely better than control. "97%" reads
exactly as it sounds.

**Winning / losing / inconclusive** — The verdict. **Winning** = over 95% chance to win. **Losing** = under 5%.
**Inconclusive** = can't tell yet, keep collecting.

**Sample ratio mismatch (SRM)** — A health check that flags when traffic wasn't split the way you set it up. A broken
split means the results can't be trusted.

**Quarantined / excluded identity** — Someone recorded in more than one variant. Set aside so they don't distort the
counts, and shown as a separate total.

**Collecting data** — Not enough data yet to report a result, so numbers are withheld rather than shown when they'd be
meaningless.

**Last computed (as-of)** — Results are computed periodically, not on every page load. This timestamp tells you how
fresh the figures are.

## Exposures

An identity is counted **once**, in the variant it saw **first**. Because exposures are deduplicated by identity and
keep only the earliest timestamp, duplicate event delivery can't inflate your counts, and each identity lands in the
time bucket of its first exposure.

If an identity is recorded against **more than one** variant (a "flicker", or bucketing that changed mid-flight), it's
**quarantined** — excluded from every variant's count and surfaced as a single excluded-identities figure. A small
number is normal; a growing one means users are slipping between variants.

The panel shows a headline total, a cumulative chart (one line per variant), a variant table (key, **Control** badge,
identities, share %), the excluded note, and a "last computed" time.

## Experiment results

For each metric, the scorecard reports how each variant did against control, using a **Bayesian** engine. Three numbers
per variant:

**Lift** — relative change vs control. Control at 4.21%, variant at 4.68% → `(4.68 − 4.21) / 4.21 ≈ +11%`.

**95% credible interval** — the range we're 95% sure the true lift sits in, drawn as a bar centred on zero:

- **Clear of zero** (e.g. +2% to +20%) → confident the variant is genuinely better (or, on the negative side, worse).
- **Crosses zero** (e.g. −3% to +14%) → inconclusive; the effect could be anything. Collect more data.

**Chance to beat control** — the same belief as one number, e.g. _97%_. Over **95%** → **winning**; under **5%** →
**losing**; in between → **inconclusive**.

:::note Why Bayesian?

"97% chance to beat control" means what it sounds like — unlike a p-value, which is routinely misread. It's also safe to
check whenever you like: peeking doesn't inflate your error rate the way repeated p-value checks do.

:::

## Sample ratio mismatch (SRM)

Before trusting a result, you need traffic to have split the way you configured. If you set 50/50 but see 9,120 in
control and 6,400 in the variant, something is broken — and if assignment is broken, every other number is suspect,
because the groups aren't comparable.

Flagsmith compares the observed split against the configured one and raises a warning when the imbalance is a
one-in-a-thousand event or rarer (it only checks once there are at least 100 identities). When it fires, **don't act on
the results** — investigate one-variant crashes, redirects that bypass bucketing, flicker, or dropped events first.

## Collecting data

Statistics on a handful of people are meaningless, so a metric shows **collecting data** until every arm has at least
**50 identities** (and, for conversion metrics, at least **5 conversions**). This stops you reading a "+300% lift" off
three conversions.

## Metric types

| Aggregation    | What it measures                               | Example                 |
| -------------- | ---------------------------------------------- | ----------------------- |
| **Occurrence** | Did the event happen at least once? (0 or 1)   | Did the user check out? |
| **Count**      | How many times the event happened per identity | Number of page views    |
| **Sum**        | The total of a numeric value across events     | Total revenue           |
| **Mean**       | The average numeric value per identity         | Average order value     |

A metric's **expected direction** (up, down, not-increase, not-decrease) tells Flagsmith which way is "good" and sorts
metrics into **goals** and **guardrails**.

## Summary

Nothing here is generally available yet — the table shows what the upcoming Enterprise beta will include.

| Capability                                      | Status                |
| ----------------------------------------------- | --------------------- |
| Exposures panel (counts, chart, share)          | In the first beta     |
| First-exposure attribution & duplicate immunity | In the first beta     |
| Quarantined (multi-variant) identities          | In the first beta     |
| Metric definitions                              | In the first beta     |
| Results scorecard: lift, credible interval      | Planned               |
| Chance to beat control & winning/losing flags   | Planned               |
| Sample ratio mismatch (SRM) check               | Planned               |
| Collecting-data floor                           | Planned               |
| Risk / decision banner / trend chart            | Not currently planned |
| Frequentist engine                              | Deferred              |

For experiment setup — multivariate flags, bucketing, identities — see
[Experimentation (A/B Testing)](/experimentation-ab-testing) and [managing identities](/flagsmith-concepts/identities).
