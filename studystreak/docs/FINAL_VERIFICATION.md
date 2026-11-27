# StudyStreak final verification checklist

Status values:

- **Verified:** checked, with the evidence given.
- **Not verified:** not checked yet, or it could not be checked in our development environment.
- **Requires manual action:** a team member has to do it, usually with real Flagsmith access.

Evidence dates refer to development on branch `feature/studystreak-experimentation`. Our development sandbox had **no
access to Flagsmith's servers and no Flagsmith keys**. Items involving the live Flagsmith **Simulation** environment
were checked by the team on their own machine, with the evidence noted. Nothing involving **Production** is marked
verified.

> **The live Simulation run is complete.** The synthetic dataset `simulation/simulated-visitors.json` (1,000 simulated
> visitors) was generated against the Flagsmith Simulation environment, validated, committed and analysed. All of its
> results are **synthetic simulation data**, not real student or Production-user results. Flagsmith's official
> experiment results remain the source of truth.

## Local application

| Item                                                                                                                                                        | Status   | Evidence                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------- |
| `npm install` has 0 vulnerabilities                                                                                                                         | Verified | `npm install` output (Milestone 7)                                                             |
| Typecheck, lint, Prettier and production build pass                                                                                                         | Verified | `npm run typecheck`, `npm run lint`, `npx prettier@3 --check .`, `npm run build` (Milestone 7) |
| All automated tests pass                                                                                                                                    | Verified | `npm test`: 257 tests in 29 files (Milestone 7)                                                |
| Landing page renders on desktop (1280×800) and mobile (iPhone 13) with no horizontal scrolling and no console errors                                        | Verified | Playwright audit (Milestone 7)                                                                 |
| Plain button shown, with no exposure, when the key is missing, Flagsmith is unreachable, the key is rejected (401), or Flagsmith hangs (fallback after 3 s) | Verified | Playwright audit (Milestone 7). Exposure behaviour covered by `SignupCta.integration.test.tsx` |
| Both variants put the button at the same position and size, with no layout shift                                                                            | Verified | Playwright: identical button boxes, layout shift 0 (Milestone 3)                               |
| Signup form: validation messages, success state, Escape closes, focus moves into the dialog                                                                 | Verified | Playwright (Milestone 4), `SignupDialog.test.tsx`                                              |
| `/api/signup` rejects invalid input (422), no cookie (400), non-JSON (415) and oversized bodies (413)                                                       | Verified | `curl` against `next start` (Milestone 4), `route.test.ts`                                     |
| `/supplementary-analysis` shows the simulated-data banner and an empty state without a dataset, and links back to `/`                                       | Verified | Playwright audit (Milestone 7)                                                                 |
| Header links (`#features`, `#how-it-works`) work                                                                                                            | Verified | Playwright audit (Milestone 7), `page.test.tsx`                                                |

## Flagsmith Simulation environment

| Item                                                                                                                                | Status                                | Evidence / action                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Simulation environment exists, and its name contains "Simulation"                                                                   | Verified                              | Team setup: environment `Simulation`, id 121260, project 56690 (read-only diagnostic)                                     |
| Managed warehouse shows **Connected**                                                                                               | Requires manual action                | §2                                                                                                                        |
| Flag `study_streak_social_proof` enabled, with variation key `social_proof` (not `Variant_1`)                                       | Verified                              | Team setup: flag 306257 on in Simulation; variation key `social_proof`                                                    |
| Three metrics created with the exact event names                                                                                    | Verified                              | Team setup: metrics 790 (`signed_up`), 791 and 792 (`signup_clicked`)                                                     |
| Experiment running at 100% rollout, 50/50, with all three metrics attached                                                          | Verified                              | Team setup: experiment 776 running, 100% rollout, 50/50; metrics 790, 791 and 792 attached                                |
| Simulator refuses a missing key, a key matching Production, invalid options, and an unreachable environment, without writing a file | Verified                              | CLI runs (Milestone 6), `credentials.test.ts`, `options.test.ts`                                                          |
| Simulator uses Flagsmith's assignment and accounts for delivered events correctly                                                   | Verified (stubbed Flagsmith API only) | `simulator.test.ts`, including the real `@flagsmith/nodejs` against a stub                                                |
| **Live `npm run simulate:traffic` run completed**                                                                                   | **Verified**                          | Team run against the Simulation environment: 1,000 synthetic visitors                                                     |
| `simulation/simulated-visitors.json` generated, validated, committed and analysed                                                   | Verified                              | Validated by the project parser; committed in `3dd36ccc1`; `npm run analyse:simulation` (synthetic results in the README) |
| Simulator summary shows confirmed counts equal to sent counts                                                                       | Verified                              | Team run: exposures 1,000/1,000, `signup_clicked` 189/189, `signed_up` 115/115 (2xx from the events API)                  |

## Production experiment readiness

| Item                                                                                                                   | Status                 | Evidence / action                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------- |
| Production warehouse **Connected**                                                                                     | Requires manual action | [FLAGSMITH_SETUP.md §2](FLAGSMITH_SETUP.md)                                                           |
| Flag, variation key and metrics match the Simulation environment                                                       | Requires manual action | §4–5                                                                                                  |
| `FLAGSMITH_CLIENT_ENVIRONMENT_KEY` and `FLAGSMITH_SERVER_KEY` set on the host. The Simulation key is **not** set there | Requires manual action | §3                                                                                                    |
| App deployed to Vercel by the team at https://studystreak-five-delta.vercel.app                                        | Not verified           | Reported by the team. Not checked from our development environment, whose network blocks `vercel.app` |
| Deployment serves branch `feature/studystreak-experimentation` and is reachable                                        | Requires manual action | Open the URL and check the Vercel deployment's commit                                                 |
| Rate limit on `POST /api/signup` at the hosting edge                                                                   | Requires manual action | README → Security and privacy                                                                         |
| Production experiment started **only after** the event-delivery checks below pass                                      | Requires manual action | §6                                                                                                    |

## Event delivery

| Item                                                                                             | Status                                            | Evidence / action                                                                                       |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Browser sends `$flag_exposure` and `signup_clicked` with the correct identity, value and headers | Verified (against a local stand-in for Flagsmith) | Playwright with DNS mapped to a local HTTPS stand-in (Milestone 4 review)                               |
| Exposure from a page closed after 0.6 s still reaches the server                                 | Verified (stand-in, headless Chromium only)       | 20 of 20 visits; Safari, Firefox and mobile not tested                                                  |
| Server sends `signed_up` and returns 201 only after a 2xx from the events API, and 502 otherwise | Verified (stub, and a real network failure)       | `record-signup-conversion.test.ts`, `route.test.ts`, `curl` returned 502 when Flagsmith was unreachable |
| Flagsmith's events API **accepts** browser events                                                | Not verified                                      | Requires manual action: DevTools check, [FLAGSMITH_SETUP.md §8](FLAGSMITH_SETUP.md)                     |
| Flagsmith's events API accepts `signed_up` from the server (201 on a deployed signup)            | Not verified                                      | Requires manual action                                                                                  |
| Warehouse shows `$flag_exposure`, `signup_clicked` and `signed_up`                               | Not verified                                      | Requires manual action                                                                                  |

## Experiment metrics

| Item                                                                              | Status                 | Evidence / action                                                                  |
| --------------------------------------------------------------------------------- | ---------------------- | ---------------------------------------------------------------------------------- |
| Code sends exactly `signed_up` (no value) and `signup_clicked` (value in seconds) | Verified               | `experiment.ts` constants, integration tests                                       |
| One `signup_clicked` event can feed both an Occurrence and a Mean metric          | Verified (source code) | `api/experimentation/results_query.py`: each metric matches its own events by name |
| Flagsmith's Mean counts non-clickers as 0                                         | Verified (source code) | `results_query.py`, `warehouses/dialect.py` (`avg_if` falls back to 0)             |
| Metrics configured in Flagsmith as documented                                     | Requires manual action | [FLAGSMITH_SETUP.md §5](FLAGSMITH_SETUP.md)                                        |
| Experiment results page shows exposures and metrics                               | Not verified           | Requires manual action                                                             |

## Statistical interpretation

| Item                                                                                     | Status                 | Evidence                                                                                          |
| ---------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------- |
| Beta quantiles, P(treatment beats control) and SRM p-values match independent references | Verified               | Tests against SciPy 1.18.1 and mpmath 1.4.1 (`beta.test.ts`, `conversion.test.ts`, `srm.test.ts`) |
| No winner is hardcoded, and the verdict needs 95% probability plus the minimum sample    | Verified               | `conversion.test.ts`                                                                              |
| Supplementary outputs are labelled "SIMULATED DATA — SUPPLEMENTARY ANALYSIS"             | Verified               | `SupplementaryReport.test.tsx`, CLI output                                                        |
| Official Flagsmith results interpreted correctly in the demo                             | Requires manual action | Read only what the results page shows ([DEMO_SCRIPT.md](DEMO_SCRIPT.md))                          |

## Privacy and security

| Item                                                                                                    | Status                 | Evidence                                                                                                     |
| ------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| Visitor cookie is a random UUID: HTTP-only, `SameSite=Lax`, and `Secure` over HTTPS                     | Verified               | `proxy.test.ts`, `curl` response headers (Milestone 2)                                                       |
| Identity comes only from the cookie, never the request body                                             | Verified               | `route.test.ts`                                                                                              |
| Name and email are not stored, logged or sent to Flagsmith                                              | Verified               | Code review; `route.test.ts` checks logs contain no personal data; events contain only the ID and event name |
| A server key can never become the browser key                                                           | Verified               | `env.test.ts`                                                                                                |
| `.env.local`, simulation backups and temporary files are ignored by Git, and no real keys are committed | Verified               | `git check-ignore`; `git grep` finds only test placeholders such as `ser.production`                         |
| Rate limiting on `/api/signup`                                                                          | Requires manual action | Hosting edge                                                                                                 |

## Hackathon demo

| Item                                                                                                 | Status                 | Evidence / action                                            |
| ---------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------ |
| Demo script written                                                                                  | Verified               | [DEMO_SCRIPT.md](DEMO_SCRIPT.md)                             |
| Both variants captured in two separate browsers or profiles (not two private windows of one browser) | Requires manual action | Flagsmith decides the variant; private windows share cookies |
| Flagsmith dashboard (flag, metrics, experiment) ready to show                                        | Requires manual action |                                                              |
| Demo recorded (3–5 minutes)                                                                          | Requires manual action |                                                              |
| "1,240" disclosed as demonstration copy in the demo                                                  | Requires manual action | The script includes the line                                 |

## Submission readiness

| Item                                                         | Status                 | Evidence / action                                                                     |
| ------------------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------------- |
| Feature branch pushed to `Subas-mohanty/flagsmith`           | Requires manual action | Not pushed. Pushing from the development session needs approval and GitHub App access |
| Pull request into `main` opened for team review              | Requires manual action |                                                                                       |
| Deployed demo URL: https://studystreak-five-delta.vercel.app | Not verified           | Deployed by the team; reachability not independently checked                          |
| Video uploaded and submission form completed                 | Requires manual action |                                                                                       |
