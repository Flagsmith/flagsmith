# First Minute

A 60-second incident drill that tests whether a short runbook helps people diagnose a checkout outage. Participants inspect a release log, service metrics and request traces, choose one diagnosis, and see where the slow request spent its time.

![Checkout incident briefing](media/first-minute.png)

[Watch the 27-second browser walkthrough](media/walkthrough.mp4)

## Play

For a no-install practice round, [download the drill](https://raw.githubusercontent.com/arpitkjaiswal/flagsmith1/main/examples/first-minute/media/first-minute.zip), unzip it and open `first-minute.html`. The debrief includes a capacity model where you can adjust the pool size and see the resulting queue growth.

To run from source, run `npm ci` and `npm run dev` with Node 24. Open the address Vite prints. Without a client-side environment key, the drill runs in practice mode. To make a portable, offline copy, run `npm run build:practice` and open `dist/first-minute.html`. Finish a round and choose **Try the other desk** to compare the layouts.

## Run the experiment locally

1. Start Flagsmith with Experimentation enabled, create an organisation, and sign in. The provided Compose setup uses PostgreSQL as the event warehouse.
2. Supply a **local Flagsmith user authentication token** with project and environment management rights in `FLAGSMITH_MANAGEMENT_TOKEN`. Use Python 3 to run `python setup_experiment.py ORGANISATION_ID` from this directory. The script creates or reuses the First Minute project, Participant drill environment, warehouse connection, feature, metric and experiment. It starts the experiment and prints one browser configuration line. Copy that line into `.env.local`. Keep management credentials outside the checkout.
3. Start or restart Vite. Its local SDK proxy forwards flags, identities and events to Flagsmith on port 8000. The briefing should say **Connected to Flagsmith**. Start the drill to enrol. For self-hosted deployments on another origin, set `VITE_FLAGSMITH_ORIGIN` to the HTTPS origin serving both the Flagsmith API and SDK events before running `npm run build`. Serve the generated `dist` directory over HTTPS.
4. Open **Experiments** in the Participant drill environment and refresh the results after events arrive. The guide is a keyed variation of the `triage_guide` multivariate flag. All eligible identities enter the experiment, with equal allocation between control and guided.

## What the experiment measures

**Hypothesis.** A three-step runbook increases the fraction of first-time participants who correctly diagnose connection-pool exhaustion within 60 seconds. Both variants use identical evidence, answer choices, time limit and feedback.

**Measurement.** The browser stores an anonymous identity and the first attempt's deadline. Opening the desk records an SDK exposure. Only a correct first answer before expiry records the `drill_resolved` occurrence event. Reloading preserves the deadline. Replays are practice. A new browser profile is a new identity.

**Evidence.** The notes panel contains a dated snapshot of a separate browser verification run. Flagsmith reported two guided exposures, one control exposure and two conversions. The automated checks deliberately exercised correct and incorrect answers. These counts establish that assignment, event delivery and aggregation work. They cannot estimate the effect on people.

**Rollout.** Collect independent participant attempts and inspect sample-ratio warnings. Flagsmith shows “Collecting data” below its inference thresholds. Once sufficient evidence supports a decision, end the participant experiment and use the same flag to roll out the selected desk. If the evidence stays inconclusive, continue collecting data.

## Submission copy

When checkout slows down, a responder often has a dashboard full of signals and has to work out what changed. First Minute lets anyone take the on-call seat. Players have 60 seconds to trace a slowdown through a release, service metrics and a slow request. Flagsmith assigns a plain desk or a three-step runbook and measures whether the player finds the root cause on their first attempt. The result helps the team decide whether every new responder should get the guide.
