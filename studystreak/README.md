# StudyStreak

StudyStreak is a student study-habit landing page built by Team Havoc for the Flagsmith Toggle Wars hackathon. It runs
one A/B test with Flagsmith Experimentation: does showing social proof next to the Sign Up button increase completed
signups?

- **Control:** a plain Sign Up button.
- **Social proof (`social_proof`):** the same button, with "🔥 1,240 students joined this week" beneath it.

The 1,240 figure is static demonstration copy, not a verified live count.

Flagsmith is the source of truth for variant assignment, exposures, conversions and the official results. The full setup
and architecture guide is still to come; this document currently covers the supplementary analysis.

## Supplementary analysis of simulated data

> **SIMULATED DATA — SUPPLEMENTARY ANALYSIS.** Everything in this section is computed from data produced by our traffic
> simulator, not from real students. It is not an official Flagsmith result and cannot show whether social proof works
> for real visitors.

We wrote our own analysis so we can check the statistics end to end on data whose true conversion rates we know. It
reads `simulation/simulated-visitors.json`, which only accepts datasets marked `"kind": "simulated"` from the
`"simulation"` environment, with every visitor ID starting `sim-`.

```bash
npm run analyse:simulation
```

The same results are shown at `/supplementary-analysis`, a page excluded from search engines, with the simulated-data
label on every section.

### Conversion rates: Bayesian beta-binomial model

Each variant's conversion rate gets a **Beta(1, 1) prior**, which is uniform: before any data, every rate from 0% to
100% is equally plausible. With `n` visitors and `k` conversions the posterior is **Beta(1 + k, 1 + n − k)**. We chose
this prior because it is neutral between the variants, and with a few hundred visitors per arm it has almost no effect
on the result. With very small samples it pulls estimates slightly towards 50%, which is why we also require a minimum
sample (below).

For signup completion (`signed_up`) and signup click-through (`signup_clicked`) we report:

| Result                        | How it is calculated                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------- |
| Conversion rate               | `k / n` for each variant                                                                                  |
| 95% credible interval         | The 2.5% and 97.5% quantiles of each posterior (exact, via the inverse incomplete beta function)          |
| Absolute difference           | Social proof rate minus control rate, in percentage points                                                |
| Relative lift                 | Absolute difference divided by the control rate                                                           |
| Intervals for the difference  | 2.5% and 97.5% quantiles of 100,000 paired posterior draws with a fixed seed, so results are reproducible |
| P(social proof beats control) | Exact closed form for two beta distributions (Evan Miller), with no sampling                              |

A credible interval reads as it sounds: given the model and the data, there is a 95% probability that the true value
lies inside it. These are Bayesian results, so we do not report p-values or "statistical significance" for the
conversion comparison.

**Supplementary verdict.** We only call a variant "likely better" when the probability is at least 95% (or at most 5%
for control). Between those it is inconclusive. Below 50 visitors and 5 conversions in each variant we report "not
enough data", whatever the probability. These thresholds mirror the ones Flagsmith documents. The code never decides a
winner in advance.

The implementation was checked against SciPy 1.18.1 (beta quantiles and chi-square p-values) and mpmath 1.4.1 (numerical
integration of P(social proof beats control)). The reference values are in the unit tests.

### Sample ratio mismatch (SRM)

The experiment is configured as a 50/50 split. We compare the observed counts with that split using a chi-square
goodness-of-fit test with one degree of freedom, and raise an **SRM warning when p < 0.001**, the threshold Flagsmith
documents. With fewer than 100 visitors the check is skipped.

An SRM warning means assignment or tracking is probably broken: for example, one variant failing to record exposures. If
it fires, do not trust the conversion results until the cause is found. A passing check is weaker evidence: it cannot
detect problems that affect both variants equally, and with small samples it can miss real imbalances. This SRM check is
a frequentist test of the traffic split, not of the treatment effect.

### Time to signup click: official and supplementary versions differ

| Version                                                                      | Who is included                    | Notes                                                                                                                                                    |
| ---------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Official Flagsmith metric: "Time to signup click (non-clickers count as 0s)" | Every exposed visitor              | A Mean metric on `signup_clicked`. Flagsmith counts visitors with no click as 0 seconds, so more clickers raises it. Its direction is **Informational**. |
| Supplementary analysis (simulated data)                                      | Only visitors who actually clicked | Mean and median seconds from first exposure to first click, plus the number of clickers in each variant.                                                 |

We confirmed the zero-filling in Flagsmith's own results query (`api/experimentation/results_query.py`): a Mean metric
averages each visitor's values, uses 0 for visitors without the event, then divides by everyone exposed. Measured that
way, a variant that persuades more people to click looks slower. That is why the official metric is Informational, and
why the supplementary version only looks at clickers. The supplementary page also shows the zero-filled figure for the
simulated data, so you can see the difference.

### Why simulated results cannot show that social proof works

The simulator decides each visitor's behaviour from conversion rates we choose. So the analysis can only show whether
our statistics recover what we put in. That makes it useful for testing the pipeline: assignment, event tracking and the
maths. It says nothing about real students, who may react to social proof very differently, or not at all.

### Assumptions and limitations

- Visitors are independent, and each has a fixed probability of converting while the experiment runs.
- Each visitor counts once, in the variant they were first assigned to.
- The 95% intervals for the difference and lift come from 100,000 Monte Carlo draws. Their last digits can vary slightly
  with the seed, but the seed is fixed, so the output is reproducible.
- Clicker-only times compare people who chose to click. If the treatment changes who clicks, those groups are not
  directly comparable.
- Only the official Flagsmith analysis covers real traffic. This analysis only reads simulated datasets.
