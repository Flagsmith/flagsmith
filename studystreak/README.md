# StudyStreak

StudyStreak is a landing page for a student study-habit tracker, built by **Team Havoc** to run one real A/B test with
Flagsmith Experimentation.

**Hackathon:** Toggle Wars: Flagsmith Experimentation Hackathon, Track 01: Test Something Real.

**Production deployment:** https://studystreak-five-delta.vercel.app (deployed to Vercel by the team). Whether it is
reachable, which commit it serves, and whether Production events reach Flagsmith have not been checked independently
from our development environment. See [docs/FINAL_VERIFICATION.md](docs/FINAL_VERIFICATION.md).

> **About "🔥 1,240 students joined this week".** This is static demonstration copy shown to the treatment group. It is
> not a verified count of real users. The page footer says so in both variants.

## Contents

- [Problem statement](#problem-statement)
- [Hypothesis](#hypothesis)
- [How StudyStreak works](#how-studystreak-works)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Flagsmith integration](#flagsmith-integration)
- [Experiment variants and metrics](#experiment-variants-and-metrics)
- [Experiment setup](#experiment-setup)
- [Local development](#local-development)
- [Environment variables](#environment-variables)
- [Traffic simulator](#traffic-simulator-simulation-environment-only)
- [Supplementary analysis of simulated data](#supplementary-analysis-of-simulated-data)
- [Testing](#testing)
- [Security and privacy](#security-and-privacy)
- [Limitations](#limitations)
- [Demo walkthrough](#demo-walkthrough)
- [Future improvements](#future-improvements)

More detail lives in [`docs/`](docs): [Flagsmith setup](docs/FLAGSMITH_SETUP.md), [demo script](docs/DEMO_SCRIPT.md) and
[final verification checklist](docs/FINAL_VERIFICATION.md).

## Problem statement

Students know that a little study every day beats cramming, but starting is the hard part. A habit app's landing page
has one job: get a hesitant student to press **Sign Up**. A common way to encourage that is social proof, showing that
other students are joining. It may help. It may also be ignored, or put people off. The only way to find out is to test
it.

## Hypothesis

> Showing social proof next to the Sign Up button will increase completed signups by at least 10% relative to a plain
> Sign Up button.

## How StudyStreak works

1. A visitor opens the landing page. On their first request they get a random anonymous ID in an HTTP-only cookie,
   reused on every later visit.
2. The browser identifies that visitor to Flagsmith. Flagsmith assigns a variant, `control` or `social_proof`, and the
   page shows it.
3. The **only** difference between variants is the line beneath the Sign Up button. Both variants render the same
   fixed-height space for it, so nothing else moves.
4. Clicking **Sign Up** opens a demo signup form that asks for a name and email. It is clearly labelled as a demo: no
   account is created and nothing is stored.
5. Three kinds of event go to Flagsmith under the same anonymous ID:
   - the **exposure**, sent when the variant is actually shown;
   - **`signup_clicked`**, sent on the first click, with the seconds since first exposure;
   - **`signed_up`**, sent from the server after a valid signup.
6. Flagsmith's Bayesian results page is the official result. A separate page, `/supplementary-analysis`, shows our own
   analysis of **simulated** traffic, clearly labelled.

## Architecture

```
Browser                                    Next.js server                         Flagsmith
───────                                    ──────────────                         ─────────
GET /  ───────────────────────────────────▶ proxy.ts: issue or reuse the
                                            studystreak_visitor_id cookie
       ◀─────────────────────────────────── layout.tsx: pass the visitor ID and
                                            client key to <Providers>
<Providers> init({ identity, enableEvents }) ─────────────────────────────────▶ identities API (variant)
useExperiment() when the variant is shown  ─────────────────────────────────▶ events API ($flag_exposure)
Sign Up click → trackEvent('signup_clicked') ───────────────────────────────▶ events API
Submit form ──────────────────────────────▶ POST /api/signup
                                            validate input, identity from cookie,
                                            @flagsmith/nodejs trackEvent('signed_up') ─▶ events API
       ◀─────────────────────────────────── 201 only after a 2xx from the events API

npm run simulate:traffic  (Simulation environment only) ─────────────────────▶ identities and events APIs
  → simulation/simulated-visitors.json → npm run analyse:simulation and /supplementary-analysis
```

| Part                        | Where                                                                                               |
| --------------------------- | --------------------------------------------------------------------------------------------------- |
| Visitor identity            | `src/proxy.ts`, `src/lib/visitor-id.ts`                                                             |
| Flagsmith browser SDK       | `src/app/providers.tsx` (start-up, flushing when the page is hidden, keepalive for event requests)  |
| Experiment state            | `src/lib/experiment.ts`, `src/lib/use-social-proof-experiment.ts`                                   |
| Variants and click tracking | `src/components/SignupCta.tsx`, `src/lib/use-signup-click-tracking.ts`, `src/lib/exposure-clock.ts` |
| Signup form                 | `src/components/SignupDialog.tsx`, `src/lib/signup.ts`                                              |
| Signup conversion           | `src/app/api/signup/route.ts`, `src/lib/server/record-signup-conversion.ts`                         |
| Simulator                   | `scripts/simulate-traffic.ts`, `src/lib/simulation/`                                                |
| Statistics                  | `src/lib/stats/`, `scripts/analyse-simulation.ts`, `src/app/supplementary-analysis/page.tsx`        |

## Technology stack

| Tool                   | Version | Used for                                                   |
| ---------------------- | ------- | ---------------------------------------------------------- |
| Next.js (App Router)   | 16.4    | Pages, the signup API route, cookie handling in `proxy.ts` |
| React                  | 19.3    | UI                                                         |
| TypeScript (strict)    | 5.9     | All code                                                   |
| Tailwind CSS           | 4.3     | Styling                                                    |
| `@flagsmith/flagsmith` | 12.6.0  | Browser SDK: assignment, exposures, `signup_clicked`       |
| `@flagsmith/nodejs`    | 9.5.0   | Server SDK: `signed_up`, traffic simulator                 |
| Vitest and jsdom       | 5.1, 31 | Unit and integration tests                                 |
| tsx                    | 4.23    | Running the simulator and analysis scripts                 |

The project was developed and tested on **Node.js 22.23**. Next.js 16 needs at least 20.9, but other versions have not
been tested, and `npm run simulate:traffic` relies on Node's `--env-file-if-exists` flag. The app lives in
`studystreak/` inside a fork of the Flagsmith monorepo and does not depend on any other part of it.

## Flagsmith integration

- **Flag:** `study_streak_social_proof`, a multivariate flag. The control is the flag's own value. One variation has the
  **key** `social_proof`.
- **Assignment:** Flagsmith buckets each identity deterministically. The app never randomises variants itself.
- **Exposure:** `useExperiment('study_streak_social_proof')` runs only in the component that renders the variant. The
  SDK records an exposure only for enrolled visitors whose flags came from Flagsmith's servers.
- **No false exposures:**
  - While flags load, the button area shows a same-sized grey placeholder and neither variant.
  - If flags fail, the key is missing, or flags take longer than 3 seconds, the plain button is shown and no exposure is
    recorded.
  - Flags that arrive after the 3-second fallback are ignored for that page view.
- **Rendering:** the page branches on the variant key (`social_proof`), not the flag value. What is shown therefore
  always matches the exposure recorded.
- **Event delivery:**
  - The browser SDK flushes every second instead of its 10-second default. It also flushes when the page is hidden or
    unloaded.
  - Event requests use `fetch` with `keepalive`, so a flush can finish after the page closes.
  - The server confirms that Flagsmith accepted `signed_up` before telling the visitor they signed up.

Step-by-step configuration: [docs/FLAGSMITH_SETUP.md](docs/FLAGSMITH_SETUP.md).

## Experiment variants and metrics

| Variant                    | What the visitor sees                                                 |
| -------------------------- | --------------------------------------------------------------------- |
| Control (`control`)        | Plain **Sign Up** button, with an empty line beneath it               |
| Treatment (`social_proof`) | The same button, with "🔥 1,240 students joined this week" beneath it |

| Metric (Flagsmith name)                         | Event            | Aggregation | Direction     | Role      |
| ----------------------------------------------- | ---------------- | ----------- | ------------- | --------- |
| Signup completion                               | `signed_up`      | Occurrence  | Up            | Primary   |
| Signup click-through                            | `signup_clicked` | Occurrence  | Up            | Secondary |
| Time to signup click (non-clickers count as 0s) | `signup_clicked` | Mean        | Informational | Secondary |

The Mean metric's name says what it does. Flagsmith's results query averages over **every** exposed visitor and counts
those who never clicked as 0 seconds (see `api/experimentation/results_query.py` in this repository). So it mixes "how
many clicked" with "how fast", and is set to Informational rather than "lower is better".

Rollout: 100% of visitors, split 50/50.

## Experiment setup

Use two Flagsmith environments in one project:

- **Production:** real visitors only, and the official results.
- **Simulation:** synthetic traffic from the simulator only.

Each needs the Flagsmith-managed warehouse, the same flag and variation key, the three metrics and the experiment. The
full procedure, including how to attach all three metrics, is in [docs/FLAGSMITH_SETUP.md](docs/FLAGSMITH_SETUP.md).

## Local development

```bash
cd studystreak
npm install
cp .env.example .env.local    # then add your keys (see below)
npm run dev                   # http://localhost:3000
```

| Command                      | What it does                                                     |
| ---------------------------- | ---------------------------------------------------------------- |
| `npm run dev`                | Development server                                               |
| `npm run build`, `npm start` | Production build and server                                      |
| `npm test`                   | All tests (Vitest)                                               |
| `npm run typecheck`          | TypeScript check                                                 |
| `npm run lint`               | ESLint                                                           |
| `npm run simulate:traffic`   | Simulated traffic through the Simulation environment (see below) |
| `npm run analyse:simulation` | Supplementary analysis of the simulated dataset                  |

Without any keys the page still works: it shows the plain button and records nothing.

## Environment variables

Real values go in `studystreak/.env.local`, which Git ignores. Never commit keys.

| Variable                           | Environment | Secret?                                   | Read by                                                                         |
| ---------------------------------- | ----------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| `FLAGSMITH_CLIENT_ENVIRONMENT_KEY` | Production  | No: the client-side key, sent to browsers | `layout.tsx`. A `ser.` key is refused, so a secret can never reach the browser. |
| `FLAGSMITH_SERVER_KEY`             | Production  | **Yes**                                   | `POST /api/signup` only. Must start with `ser.`.                                |
| `FLAGSMITH_SIMULATION_SERVER_KEY`  | Simulation  | **Yes**                                   | `npm run simulate:traffic` only. Never set it on the deployed app.              |

The client key is read on the server when the app runs and passed to the page, so changing it needs a restart, not a
rebuild.

## Traffic simulator (Simulation environment only)

The simulator sends synthetic visitors through the **Simulation** environment, so the experiment, its metrics and
Flagsmith's own results can be exercised end to end without touching real traffic.

```bash
# studystreak/.env.local must hold FLAGSMITH_SIMULATION_SERVER_KEY (the Simulation environment's server-side key)
npm run simulate:traffic
npm run simulate:traffic -- --visitors 1000 --seed 20261129 --control-signup-rate 0.10 --social-proof-signup-rate 0.12
```

Other options: `--click-to-signup-rate` (share of clickers who sign up, default 0.6) and `--median-click-seconds`
(default 8). Invalid or unknown options stop the run.

For each visitor the simulator:

1. Creates an identity `sim-s<seed>-<number>`.
2. Calls `getExperimentFlag('study_streak_social_proof', identity)` from `@flagsmith/nodejs`. **Flagsmith assigns the
   variant** and the SDK records the `$flag_exposure` event. The simulator never picks a variant; visitors Flagsmith
   does not enrol are left out and counted.
3. Decides, from the seed alone, whether the visitor clicks and signs up, using the configured rates. Click times follow
   a log-normal distribution around the median.
4. Sends `signup_clicked` (value: seconds to click) and `signed_up` with `trackEvent`, under the same identity.

Events are flushed every 50 visitors so the SDK's buffer never overflows. The client is closed at the end so everything
buffered is sent.

**Safety checks.**

- The simulator reads only `FLAGSMITH_SIMULATION_SERVER_KEY`, which must be a `ser.` key. It refuses a key that matches
  `FLAGSMITH_SERVER_KEY` or `FLAGSMITH_CLIENT_ENVIRONMENT_KEY`, and never falls back to another variable.
- Before sending anything, it reads the environment's name from Flagsmith. It refuses any name containing "prod" or
  "production", and any name that does not contain "Simulation".
- It stops with a setup error in any of these cases:
  - the flag is missing or disabled;
  - no experiment is running;
  - Flagsmith returns a variant other than `control` or `social_proof`;
  - more than 5% of assignment requests fail.
- Keys are never printed.

**Event delivery.** The SDK's `flushEvents()` and `close()` never report failures, so the simulator watches the events
API's responses. An event counts as **confirmed** only when its batch received a 2xx response. The summary and dataset
record, for each event, how many were sent to the SDK and how many Flagsmith confirmed.

**Output.**

- The run is validated with the same parser the analysis uses, then written to `simulation/simulated-visitors.json`.
- Any existing file is first copied to `simulated-visitors.backup-<time>.json`, and the new file is swapped in
  atomically.
- Backups and temporary files are ignored by Git.

**Reproducibility.** A seed fixes every visitor's identity and behaviour. Flagsmith bucketing is deterministic per
identity, so the same seed against the same experiment produces the same dataset. Rerunning a seed resends identical
events for identities Flagsmith has already seen. That changes no metric: exposures and Occurrence metrics count each
visitor once, and repeated identical click times leave each visitor's Mean unchanged.

**Status:** the simulator has been tested against a stubbed Flagsmith API but **has not yet been run against a live
Simulation environment**. No `simulation/simulated-visitors.json` is committed yet.

## Supplementary analysis of simulated data

> **SIMULATED DATA — SUPPLEMENTARY ANALYSIS.** Everything in this section is computed from data produced by our traffic
> simulator, not from real students. It is not an official Flagsmith result and cannot show whether social proof works
> for real visitors.

We wrote our own analysis to check the statistics end to end on data whose true conversion rates we know.

- It reads `simulation/simulated-visitors.json`.
- It only accepts datasets marked `"kind": "simulated"` from the `"simulation"` environment, with every visitor ID
  starting `sim-`.

```bash
npm run analyse:simulation
```

The same results are shown at `/supplementary-analysis`. That page is excluded from search engines and shows the
simulated-data label on every section. Until a dataset exists, it says so and shows no numbers.

### Conversion rates: Bayesian beta-binomial model

Each variant's conversion rate gets a **Beta(1, 1) prior**, which is uniform: before any data, every rate from 0% to
100% is equally plausible. With `n` visitors and `k` conversions the posterior is **Beta(1 + k, 1 + n − k)**.

We chose this prior because it is neutral between the variants. With a few hundred visitors per arm it has almost no
effect on the result. With very small samples it pulls estimates slightly towards 50%, which is one reason for the
minimum sample below.

For signup completion (`signed_up`) and signup click-through (`signup_clicked`) we report:

| Result                        | How it is calculated                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------- |
| Conversion rate               | `k / n` for each variant                                                                                  |
| 95% credible interval         | The 2.5% and 97.5% quantiles of each posterior (exact, via the inverse incomplete beta function)          |
| Absolute difference           | Social proof rate minus control rate, in percentage points                                                |
| Relative lift                 | Absolute difference divided by the control rate                                                           |
| Intervals for the difference  | 2.5% and 97.5% quantiles of 100,000 paired posterior draws with a fixed seed, so results are reproducible |
| P(social proof beats control) | Exact closed form for two beta distributions (Evan Miller), with no sampling                              |

**Reading the numbers.**

- A 95% credible interval means: given the model and the data, there is a 95% probability that the true value lies
  inside it.
- If the interval for the lift includes 0%, the data are consistent with no effect.
- These are Bayesian results, so we do not report p-values or "statistical significance" for the conversion comparison.

**Supplementary verdict.**

- A variant is called "likely better" only when the probability is at least 95%, or at most 5% for control. Between
  those it is inconclusive.
- Below 50 visitors and 5 conversions in each variant, the verdict is "not enough data", whatever the probability.
- These thresholds mirror the ones Flagsmith documents. The code never decides a winner in advance.

The implementation was checked against SciPy 1.18.1 (beta quantiles and chi-square p-values) and mpmath 1.4.1 (numerical
integration of P(social proof beats control)). The reference values are in the unit tests.

### Sample ratio mismatch (SRM)

The experiment is configured as a 50/50 split. We compare the observed counts with that split using a chi-square
goodness-of-fit test with one degree of freedom. An **SRM warning** is raised when p < 0.001, the threshold Flagsmith
documents. With fewer than 100 visitors the check is skipped.

An SRM warning means assignment or tracking is probably broken, for example one variant failing to record exposures. If
it fires, do not trust the conversion results until the cause is found.

A passing check is weaker evidence:

- it cannot detect problems that affect both variants equally;
- with small samples it can miss real imbalances.

This SRM check is a frequentist test of the traffic split, not of the treatment effect.

### Time to signup click: official and supplementary versions differ

| Version                                                                      | Who is included                    | Notes                                                                                                                                                    |
| ---------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Official Flagsmith metric: "Time to signup click (non-clickers count as 0s)" | Every exposed visitor              | A Mean metric on `signup_clicked`. Flagsmith counts visitors with no click as 0 seconds, so more clickers raises it. Its direction is **Informational**. |
| Supplementary analysis (simulated data)                                      | Only visitors who actually clicked | Mean and median seconds from first exposure to first click, plus the number of clickers in each variant.                                                 |

We confirmed the zero-filling in Flagsmith's own results query (`api/experimentation/results_query.py`). A Mean metric
averages each visitor's values, uses 0 for visitors without the event, then divides by everyone exposed. Measured that
way, a variant that persuades more people to click looks slower.

That is why the official metric is Informational, and why the supplementary version only looks at clickers. The
supplementary page also shows the zero-filled figure for the simulated data, so you can see the difference.

### Why simulated results cannot show that social proof works

The simulator decides each visitor's behaviour from conversion rates we choose. So the analysis can only show whether
our statistics recover what we put in. That makes it useful for testing the pipeline: assignment, event tracking and the
maths. It says nothing about real students, who may react to social proof very differently, or not at all.

### Assumptions

- Visitors are independent, and each has a fixed probability of converting while the experiment runs.
- Each visitor counts once, in the variant they were first assigned to.
- The 95% intervals for the difference and lift come from 100,000 Monte Carlo draws. Their last digits could vary with
  the seed, but the seed is fixed, so the output is reproducible.
- Clicker-only times compare people who chose to click. If the treatment changes who clicks, those groups are not
  directly comparable.
- Only the official Flagsmith analysis covers real traffic. This analysis only reads simulated datasets.

## Testing

```bash
npm test             # 257 tests
npm run typecheck
npm run lint
npx prettier@3 --check .   # uses the repository's root .prettierrc.json
npm run build
```

**What the tests cover:**

- **Identity:** the visitor cookie and the proxy.
- **Configuration:** client, server and Simulation keys, including that a server key can never reach the browser.
- **Experiment state:** loading, unavailable and ready.
- **Variants:** the buttons are byte-identical and the reserved space is the same in every state.
- **Exposure, with the real SDK and network stubbed:**
  - nothing is recorded while loading, after a failure, or after the 3-second timeout;
  - exactly one exposure per visitor otherwise.
- **Events:**
  - `signup_clicked`: first click only, measured from first exposure, surviving a reload;
  - flushing when the page is hidden, with listeners removed afterwards;
  - `keepalive` is added only to event requests.
- **Signup:** the form's validation, double-submit protection and error states. The API route's input checks, body-size
  limit and cookie-only identity, and its refusal to report success unless Flagsmith confirmed the event.
- **Statistics:** checked against SciPy and mpmath reference values.
- **SRM and time to click:** both versions of the time-to-click figure, and dataset validation.
- **Simulator:**
  - credential and environment-name checks, and use of Flagsmith's own assignment;
  - event names and values, and delivery accounting;
  - safe file replacement and reproducibility, run against both a fake client and the real Node SDK.

No test needs real credentials or network access.

## Security and privacy

- **Visitor identity:**
  - The cookie holds a random UUID (HTTP-only, `SameSite=Lax`, `Secure` over HTTPS) and nothing else.
  - No IP addresses or device fingerprints are used.
  - The server takes the identity only from the cookie, never from the request body.
- **Signup data:** the name and email are validated and then discarded. They are not stored, logged or sent to
  Flagsmith; only the anonymous ID and event name are.
- **Keys:**
  - Server-side keys stay on the server, and a `ser.` key is refused as the client key.
  - The simulator refuses Production keys and non-Simulation environments.
  - Nothing prints a key.
- **Signup endpoint hardening:** it accepts JSON only, rejects bodies over 2 KB, and returns generic error messages.
- **Rate limiting:** `/api/signup` has none. Add a rate limit at your hosting edge, for example a firewall rule on
  `POST /api/signup`.
- **Simulated data:** the simulated dataset contains only synthetic `sim-` identities and generated behaviour.

## Limitations

- **The social-proof figure is not real.** "1,240 students joined this week" is static demonstration copy.
- **The signup is a demo.** It records a conversion but creates no account.
- **Event delivery from the browser is best effort.**
  - Page-hide flushing and `keepalive` delivered every exposure from pages closed after 0.6 s, in headless Chromium
    against a local stand-in for Flagsmith.
  - This was not tested on Safari, Firefox, mobile devices or Flagsmith's real servers.
  - Crashes and lost connections can still lose events.
- **Not verified against live Flagsmith.** The integration was tested with stubbed and stand-in Flagsmith APIs. Events
  arriving in a real warehouse and the official results page still need checking with real keys (see
  [docs/FINAL_VERIFICATION.md](docs/FINAL_VERIFICATION.md)).
- **No live simulation yet.** The simulator has not been run against a live Simulation environment, so there is no
  committed simulated dataset yet.
- **Clock differences.** Exposures are timestamped by the visitor's browser and `signed_up` by the server. Flagsmith
  only counts conversions after the first exposure, so a browser clock running well ahead of the server could cause a
  signup to be ignored.
- **Click de-duplication relies on `localStorage`.** Clearing site data allows a second `signup_clicked`.
- **The Mean metric mixes rate and speed.** Flagsmith's version is zero-filled (see above), so it is Informational.
- **Hosting.** The team has deployed the app to Vercel (link above), but its reachability and Production event delivery
  have not been verified independently. Rate limiting must still be added at the hosting layer.

## Demo walkthrough

A full 3–5 minute script, including what to show on each screen, is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). In
short:

1. Open `/`, introduce the problem and the hypothesis.
2. Show the control and social-proof variants. Use two separate browsers or profiles: private windows of one browser
   share cookies, and so show the same variant. Or delete the `studystreak_visitor_id` cookie and reload until both have
   appeared.
3. Click **Sign Up** and walk through the demo form and its disclosure.
4. Show the events in DevTools → Network (`events.api.flagsmith.com`).
5. Show the experiment, metrics and results in the Flagsmith dashboard.
6. Show `/supplementary-analysis` and explain it is simulated, supplementary and not the official result.
7. Close with the limitations.

## Future improvements

- **Real social-proof count:** replace the static figure with a real, verified count, or remove it once the experiment
  ends.
- **Rate limiting:** add a rate limit on `/api/signup` at the hosting edge.
- **Event delivery:** use `navigator.sendBeacon` or an SDK-level unload flush if Flagsmith adds one (tracked upstream in
  [Flagsmith/flagsmith-js-client#445](https://github.com/Flagsmith/flagsmith-js-client/issues/445)).
- **End-to-end tests:** add Playwright tests in CI against a stand-in Flagsmith API.
- **Real signup:** once the experiment ends, build real signup and the streak tracker itself.
