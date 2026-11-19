# First Minute

A 60-second incident drill that tests whether a short runbook helps people diagnose a checkout outage. Participants inspect a release log, service metrics and request traces, choose one diagnosis, and see where the slow request spent its time.

![Checkout incident briefing](media/first-minute.png)

[Watch the 38-second captioned walkthrough](media/walkthrough.mp4)

## Play

For a no-install practice round, [download the drill](https://raw.githubusercontent.com/Flagsmith/flagsmith/035de2312d49460031ab93af09f91ddb7a77363e/examples/first-minute/media/first-minute.zip), unzip it and open `first-minute.html`. The debrief includes a capacity model where you can adjust the pool size and see the resulting queue growth.

To run from source, run `npm ci` and `npm run dev` with Node 24. Open the address Vite prints. Without a client-side environment key, the drill runs in practice mode. To make a portable, offline copy, run `npm run build:practice` and open `dist/first-minute.html`. Finish a round and choose **Try the other desk** to compare the layouts.

The download is pinned to the commit that packaged it. Its SHA-256 is `8b23c21fd4b40a30e4fb50b2d2b049629dbf58f2b557d7c8b8d3aeadf485a4e8`. To reproduce `media/first-minute.zip`, run `npm run package:practice` with Node 24 and Python 3 installed. When publishing a new archive, update both README links to its commit and record its checksum here.

## Run the experiment locally

1. From the repository root, run `docker compose up -d`. Open `http://localhost:8000`, sign in and create an organisation if this is a fresh install. The supplied Compose file enables Experimentation and stores SDK events in PostgreSQL.
2. From `examples/first-minute`, run `python3 setup_experiment.py` in a terminal. Sign in with your local Flagsmith email and password. If your account belongs to several organisations, the script lists their names and IDs so you can rerun it with the chosen ID. It creates or reuses the First Minute project, Participant drill environment, warehouse connection, flag, metric and experiment. Copy the two printed `VITE_` lines into `.env.local`. For unattended setup, provide your local user token in `FLAGSMITH_MANAGEMENT_TOKEN` and run `python3 setup_experiment.py ORGANISATION_ID`.
3. Start or restart Vite. Its local SDK proxy forwards flags, identities and events to Flagsmith on port 8000. The briefing should say **Connected to Flagsmith**. Start the drill to enrol. For a shared deployment, set `VITE_FLAGSMITH_ORIGIN` to the HTTPS origin serving the Flagsmith API and SDK events. Set `VITE_FLAGSMITH_DASHBOARD_URL` to the address where your team signs in to view that experiment. Run `npm run build` and serve `dist` over HTTPS.
4. Open **Experiments** in the Participant drill environment and refresh the results after events arrive. The guide is a keyed variation of the `triage_guide` multivariate flag. All eligible identities enter the experiment, with equal allocation between control and guided.

If the self-hosted dashboard shows **Maintenance** because its bootstrap request is blocked, configure `FLAGSMITH_ON_FLAGSMITH_API_URL` and `FLAGSMITH_ON_FLAGSMITH_API_KEY` on the web service to read from a local dashboard configuration environment, then restart the service. [Self-hosting guide](../../docs/docs/deployment-self-hosting/core-configuration/running-flagsmith-on-flagsmith.md)

## What the experiment measures

**Hypothesis.** A three-step runbook increases the fraction of first-time participants who correctly diagnose connection-pool exhaustion within 60 seconds. Both variants use identical evidence, answer choices, time limit and feedback.

**Measurement.** Opening the first desk fixes eligibility for this browser. If a player starts in offline practice, later rounds on the same site stay in practice. Reading the briefing keeps the player eligible. An enrolled player gets 60 seconds from the moment the browser claims the desk. Reloading or opening another tab preserves the original assignment and deadline. A new browser profile or a separately downloaded file has its own storage.

The browser saves the first answer before showing the solution. If the participant site cannot read or save the first desk, it keeps the briefing open and offers a retry. The standalone download remains playable with browser storage disabled.

The participant site retries interrupted exposures and correct first-answer events with the original identity, variation and timestamps. When Flagsmith accepts an event, its receipt ends the retry. Flagsmith rejects events older than ten days. If its receipt reports that the delivery window has closed, the drill keeps the local result and tells the player. The warehouse counts exposed identities and whether each one resolved the drill. Replaying the same event after a lost acknowledgement preserves those counts.

**Evidence.** A separate automated run against local Flagsmith recorded three exposures and two conversions in the QA environment. The checked-in Playwright suite intercepts SDK requests to test browser behaviour. The in-app **Experiment replay** uses warehouse results from 240 synthetic identities that the rehearsal script sent through the SDK to local Flagsmith. [QA snapshot](verification.json) · [Rehearsal results](rehearsal.json)

**Rollout.** Collect independent participant attempts and inspect sample-ratio warnings. Flagsmith shows “Collecting data” below its inference thresholds. Once sufficient evidence supports a decision, end the participant experiment and use the same flag to roll out the selected desk. If the evidence stays inconclusive, continue collecting data.

## Replay the Flagsmith experiment

Open **Experiment replay** in the drill. Assignment shows how the multivariate flag split 240 simulated identities. Results compares 83 conversions from 114 guided attempts with 54 from 126 standard attempts. The script programmed a 72% success chance for guided and 45% for standard. Flagsmith calculated the conversion rates, relative lift and win probability for this synthetic sample. Human outcomes are measured in the **Participant drill** environment.

Rollout shows what happened after the synthetic experiment closed. The same `triage_guide` flag was set to 100% guided in **Synthetic rollout rehearsal**. All 16 post-rollout SDK checks received the guided desk outside the experiment. The replay and its downloadable data work offline.

![Completed synthetic experiment in the native Flagsmith dashboard](media/flagsmith-results.png)

To reproduce the capture, run the following from this directory against the local Flagsmith instance. It accepts the same sign-in and optional organisation ID as the participant setup.

```sh
python3 rehearse.py
```

This command provisions the dedicated rehearsal environment. It sends seeded traffic through the JavaScript SDK, waits for the warehouse counts to match, and uses the Flagsmith results to select a desk. Results refreshes respect the server's five-minute cooldown. The script pauses enrolment before closing the rehearsal and updating the environment default. Each run against a completed rehearsal verifies the rollout with 16 fresh identities. The JSON contains aggregate evidence only. The allocation check uses an exact two-sided binomial test against 50/50 when Flagsmith leaves its sample-ratio statistic empty.

The [captured JSON](rehearsal.json) drives the replay. To replace it after your own successful run, save the command output to a temporary file, then move it to `rehearsal.json`. The dashboard capture is a separate image taken from the original run shown here.

## Browser checks

Run `npx playwright install chromium` once, then `npm test`. To use an existing Chromium installation, set `CHROMIUM_EXECUTABLE` to its path. The browser tests intercept SDK traffic locally and cover simultaneous submissions, interrupted connections, keyboard navigation, timeouts and practice exclusions. The rehearsal command above exercises the real API and warehouse.

With pytest installed, run `python3 -m pytest tests/test_rehearsal.py` to check recovery when Flagsmith asks the rehearsal to wait before refreshing results.

## Submission copy

When checkout slows down, a responder often has a dashboard full of signals and has to work out what changed. First Minute lets anyone take the on-call seat. Players have 60 seconds to trace a slowdown through a release, service metrics and a slow request. Flagsmith assigns a plain desk or a three-step runbook and measures whether the player finds the root cause on their first attempt. The result helps the team decide whether every new responder should get the guide.
