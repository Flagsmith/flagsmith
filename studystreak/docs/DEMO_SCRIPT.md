# StudyStreak demo script (3–5 minutes)

**Toggle Wars: Flagsmith Experimentation Hackathon, Track 01: Test Something Real.** Team Havoc.

Ground rule: **only say what the screen shows.** Do not state or imply a winning variant unless Flagsmith's results page
shows a conclusive result at the time of recording. If the results show "Collecting data" or "Inconclusive", say so;
that is an honest and valid outcome.

## Before recording

- [ ] The deployed app (or `npm run build && npm start` locally) has Production keys and loads the plain or social-proof
      button.
- [ ] Two private browser windows are open on the site, one showing **control** and one showing **social proof**. To get
      the other variant, close the private window and open a new one; that clears the visitor cookie. Repeat until you
      have both. Flagsmith decides the variant, so you cannot pick it.
- [ ] DevTools → Network is open in one window, filtered to `events.api.flagsmith.com`.
- [ ] The Flagsmith dashboard is open on: **Metrics**, the **Production experiment** page, and **Environment Settings ›
      Warehouse**.
- [ ] `/supplementary-analysis` is open. If there is no simulated dataset yet, it shows "No simulated dataset yet". Say
      so rather than skipping it.
- [ ] Note down the exact numbers shown in Flagsmith at recording time. Do not prepare numbers in advance.

## Script

### 0:00–0:25 · The problem (screen: landing page, top)

> "Students know daily study works, but starting is hard. StudyStreak is a study-habit app, and its landing page has one
> job: get a hesitant student to press Sign Up. A popular trick is social proof, showing that others are joining. Does
> it actually work? We tested it with Flagsmith Experimentation instead of guessing."

### 0:25–0:50 · The hypothesis (screen: landing page, scroll through features and how it works)

> "Our hypothesis: showing social proof next to the Sign Up button increases completed signups by at least 10% relative
> to a plain button. The primary metric is completed signups, recorded as the event `signed_up`."

### 0:50–1:30 · The two variants (screen: the two private windows side by side)

Point at the button and the line beneath it in each window.

> "Flagsmith assigns each anonymous visitor to a variant: control gets the plain button, social proof gets the same
> button with '1,240 students joined this week'. That number is demonstration copy, not a real count, and the footer
> says so. The message is the **only** difference. Both variants reserve the same space under the button, so the button
> never moves and the layout is identical. While flags load, neither variant is shown, and if Flagsmith is unavailable
> the plain button appears without being counted in the experiment."

### 1:30–2:10 · Signup flow and event tracking (screen: one window with DevTools → Network)

1. Point at the `POST /v1/events` request containing `$flag_exposure`.

   > "When the variant is actually shown, the SDK records an exposure for this visitor's anonymous ID."

2. Click **Sign Up**, then point at the new request containing `signup_clicked`.

   > "The first click sends `signup_clicked`, with the seconds since this visitor first saw the variant. Repeat clicks
   > aren't counted."

3. Submit the empty form to show the validation, then submit a test name and email.

   > "The form is a demo: no account is created and nothing is stored. The server checks the input, then sends
   > `signed_up` to Flagsmith with the same anonymous ID. It only shows success after Flagsmith confirms it accepted the
   > event."

### 2:10–3:10 · Flagsmith (screen: Flagsmith dashboard)

1. **Flag:** show `study_streak_social_proof`, its control value and the `social_proof` variation key.

   > "One multivariate flag; the variation key is what the app branches on."

2. **Metrics:** show the three metrics.

   > "Signup completion is the primary metric, and click-through is secondary. Time to click is a Mean metric, and
   > Flagsmith counts non-clickers as zero seconds. So it mixes how many clicked with how fast, and we set it to
   > Informational on purpose."

3. **Experiment page:** show 100% rollout, the 50/50 split, the Exposures panel and the results table. Read out only
   what is shown:
   - "Collecting data": "Each variant needs at least 50 visitors and 5 conversions before Flagsmith reports a result.
     We're not there yet."
   - Numbers shown: "The social-proof lift is _[read from screen]_, with a 95% credible interval of _[read]_ and a win
     probability of _[read]_."
   - If the interval crosses zero: "The interval includes zero, so this is inconclusive. We don't call a winner."
   - **Sample ratio mismatch** warning: "Traffic didn't split as configured, so we wouldn't trust these numbers yet."

### 3:10–4:00 · Supplementary analysis (screen: `/supplementary-analysis`)

Point at the amber **SIMULATED DATA — SUPPLEMENTARY ANALYSIS** banner first.

> "This page is not our result. It runs our own statistics on simulated visitors sent through a separate Flagsmith
> Simulation environment, so we can check our pipeline on data whose true rates we set ourselves."

- **If a dataset exists:**

  > "Flagsmith assigned the variants, and the simulator was set to 10% and 12% signup rates; those are inputs, not
  > findings. With a Beta(1,1) prior, the 95% credible interval is the range where the true rate or lift lies with 95%
  > probability. If the lift interval includes zero, we can't claim an effect. P(social proof beats control) is the
  > posterior probability. The sample ratio check tests the 50/50 split."

- **If no dataset exists:** "We haven't completed a live Simulation run yet, so this page correctly shows no numbers."

### 4:00–4:40 · Limitations and conclusion (screen: README, Limitations section, or the landing page)

> "To be clear about what we haven't proven: the social-proof figure is demo copy, the signup is a demo, and browser
> event delivery is best effort. Simulated results say nothing about real students; only Flagsmith's Production results
> can answer the question. What we built is a correct experiment: identical layouts, deterministic assignment, no false
> exposures, server-confirmed conversions, and honest statistics. The result is whatever Flagsmith shows, including 'not
> enough data yet'."

## Likely judge questions

| Question                                                            | Answer                                                                                                                                                                                                      |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| How do you know both variants are identical apart from the message? | A test asserts the button markup is byte-identical across variants and that the message space is the same height in every state. The browser check showed the button in the same position and size in both. |
| What if a visitor sees the variant before flags load?               | Nothing variant-specific is shown until Flagsmith answers, and after 3 seconds the plain button is shown with no exposure recorded.                                                                         |
| Could a signup be counted twice?                                    | Signup completion is an Occurrence metric, so each visitor counts at most once, even if an event is retried.                                                                                                |
| Why is time-to-click Informational?                                 | Flagsmith's Mean counts non-clickers as 0 s, so a variant with more clickers looks slower. The supplementary page shows the clicker-only figures.                                                           |
| Why Bayesian?                                                       | Flagsmith's engine is Bayesian. Our supplementary analysis uses a Beta-Binomial model so the two use the same concepts: credible intervals and win probability, no p-values.                                |
| Is the 1,240 real?                                                  | No. It is static demonstration copy, disclosed in the footer, the README and this demo.                                                                                                                     |
