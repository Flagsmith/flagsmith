# Flagsmith setup for StudyStreak

This guide configures Flagsmith **Cloud** (app.flagsmith.com) for the `study_streak_social_proof` experiment. It is
based on the Flagsmith Experimentation documentation and on the dashboard and API source code in this repository
(`docs/docs/experimentation/`, `frontend/web/components/experiments/`, `api/experimentation/`).

**Status:**

| Environment    | Status                                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------------------- |
| **Simulation** | **Set up and used.** The team completed these steps and ran the simulator against it (see FINAL_VERIFICATION).  |
| **Production** | **Not set up.** No Production experiment exists yet. Follow section 6's Production steps, in order, when ready. |

Record each result in [FINAL_VERIFICATION.md](FINAL_VERIFICATION.md). Simulation results are synthetic and are never
reported as real-user results.

Flagsmith Experimentation is in beta. If the dashboard differs from what is described here, follow the dashboard and
note the difference.

## 1. Project and environments

1. Create a project, for example `StudyStreak`, and check that the left-hand menu has **Experiments** and **Metrics**.
   If it does not, Experimentation is not enabled for your organisation.
2. Create two environments in that project:

| Environment    | Name                                         | Receives                              |
| -------------- | -------------------------------------------- | ------------------------------------- |
| **Production** | `Production` (must not contain "Simulation") | Real visitors only. Official results. |
| **Simulation** | exactly `Simulation`                         | `npm run simulate:traffic` only.      |

The simulator reads the name of the environment behind its key and runs only if that name is exactly `Simulation`
(ignoring case and surrounding spaces). Every other name is refused, including `SimulationProduction`,
`StudyStreak Simulation` and `Development`, and any name containing "prod" is reported as Production. Never point the
simulator at Production, or the app at Simulation.

## 2. Warehouse (each environment)

Events and results need a warehouse, and experiments cannot be created without one.

1. Open **Environment Settings › Warehouse**.
2. Select **Flagsmith** (the managed warehouse) and click **Enable**, then confirm.
3. Click **Send your first event**. The status moves from **Created** to **Pending Connection**, then to **Connected**
   once the first event has been processed. **This can take a few hours**, so do it first.
4. Once connected, the warehouse card shows the total events received and the number of unique event names. That is the
   quickest way to see events arriving (step 8).

Connecting your own ClickHouse, Databricks or PostgreSQL instead needs a Scale-Up or Enterprise plan on Flagsmith Cloud.
StudyStreak does not need it.

## 3. Keys

Each environment has its own keys. Copy them from the environment's settings: the client-side key is on the Environment
settings page, and server-side keys are under **Environment settings → SDK Keys**.

| Variable in `studystreak/.env.local` | Which key                                           | Secret?               |
| ------------------------------------ | --------------------------------------------------- | --------------------- |
| `FLAGSMITH_CLIENT_ENVIRONMENT_KEY`   | **Production** client-side environment key          | No (sent to browsers) |
| `FLAGSMITH_SERVER_KEY`               | **Production** server-side key (starts with `ser.`) | **Yes**               |
| `FLAGSMITH_SIMULATION_SERVER_KEY`    | **Simulation** server-side key (starts with `ser.`) | **Yes**               |

Never put a key in chat, code, documentation or Git. `.env.local` is ignored by Git. On a hosting platform, set
`FLAGSMITH_CLIENT_ENVIRONMENT_KEY` and `FLAGSMITH_SERVER_KEY` only. The Simulation key belongs only on the machine that
runs the simulator.

The app refuses a `ser.` key as the client key, and refuses a server key that does not start with `ser.`. The simulator
refuses a Simulation key that matches either Production variable.

## 4. Feature flag

Flags belong to the project; each environment has its own state for them.

1. Create a **multivariate** flag named exactly `study_streak_social_proof`.
2. Set the flag's own value to `control`. This value is the **control** variant, and Flagsmith reserves the key
   `control` for it.
3. Add one variation:
   - **Value:** `🔥 1,240 students joined this week`. The app does not read this value; it renders the message from
     code, based on the variation key.
   - **Key:** `social_proof`, typed exactly. **If you leave the key empty, the dashboard saves `Variant_1`.** The app
     would then never show the treatment, so the experiment would be broken.
   - **Weight:** 0. The experiment sets the split.
4. Enable the flag in **both** environments.

With the Flagsmith CLI, the documented equivalent is:

```bash
flagsmith feature create study_streak_social_proof --value control --enabled
flagsmith feature variant add study_streak_social_proof --value "🔥 1,240 students joined this week" --key social_proof --weight 0
flagsmith feature get study_streak_social_proof --json    # check the variation key is social_proof
```

## 5. Metrics (each environment)

Metrics belong to an environment, so create all three in **Production and Simulation**: **Metrics › Create Metric**.
Event names are case-sensitive.

| Name                                              | What do you want to measure? | Direction                    | Event name       |
| ------------------------------------------------- | ---------------------------- | ---------------------------- | ---------------- |
| `Signup completion`                               | Occurrence                   | Higher is better             | `signed_up`      |
| `Signup click-through`                            | Occurrence                   | Higher is better             | `signup_clicked` |
| `Time to signup click (non-clickers count as 0s)` | Mean                         | Neither — informational only | `signup_clicked` |

The two `signup_clicked` metrics share one event, and Flagsmith matches each metric to its events by name. The Mean
metric averages the event's `value`, which is the seconds since first exposure. Flagsmith counts visitors without the
event as 0, which is why it is Informational. The README explains this in more detail.

## 6. Experiment (each environment)

Settings for both environments:

| Setting        | Value                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Name           | `study_streak_social_proof`                                                                                                                 |
| Hypothesis     | Showing social proof next to the signup button will increase completed signup conversion by at least 10% relative to a plain signup button. |
| Feature flag   | `study_streak_social_proof`                                                                                                                 |
| Rollout        | 100%                                                                                                                                        |
| Split          | 50/50 (**Split evenly**): `control` 50%, `social_proof` 50%                                                                                 |
| Primary metric | Signup completion, expected to **increase**                                                                                                 |
| Other metrics  | Signup click-through (expected to increase), and Time to signup click (Informational)                                                       |

### Two facts that affect the order of work

- **The dashboard wizard attaches only one metric**, the primary one, in its Measurement step.
- **Creating an experiment in the dashboard starts it immediately**, unless your account has experiment lifecycle states
  enabled. The wizard creates the experiment with its rollout disabled, then calls `/start/` straight away, and starting
  is what enables the rollout and lets visitors into the variants
  (`frontend/web/components/experiments/CreateExperimentWizard.tsx`, `enable_experiment_rollout` in
  `api/experimentation/services.py`). A running experiment locks the flag's configuration and variations.

### Simulation environment (done)

The team created this experiment in the dashboard (**Experiments › Create Experiment**), which started it straight away.
That is acceptable only because Simulation receives synthetic traffic:

1. **Setup:** name, hypothesis, flag.
2. **Rollout:** 100%, **Split evenly**.
3. **Measurement:** Signup completion, **Increase**.
4. **Review & Launch.**

Then attach the two other metrics (section 7).

### Production environment (not done yet)

**Visitors must not enter the Production experiment until every readiness check has passed.** So the Production
experiment is created **with its rollout disabled**, and nothing is started until the checks pass.

**Do not use the dashboard wizard for Production** unless experiment lifecycle states are enabled for your account:
without them, the wizard starts the experiment, and enables its rollout, as soon as it is created.

1. **Create it through the API, disabled.** This attaches all three metrics and leaves the experiment stopped, with its
   rollout override disabled, so no visitor is enrolled and no exposure is recorded:

   ```bash
   # Body for: flagsmith api api/v1/environments/<PRODUCTION_ENV_KEY>/experiments/ --input -
   {
     "feature": <flag id>,
     "name": "study_streak_social_proof",
     "hypothesis": "Showing social proof next to the signup button will increase completed signup conversion by at least 10% relative to a plain signup button.",
     "metrics": [
       { "metric": <Signup completion id>, "expected_direction": "increase" },
       { "metric": <Signup click-through id>, "expected_direction": "increase" },
       { "metric": <Time to signup click id>, "expected_direction": "not_increase" }
     ],
     "experiment_rollout": {
       "enabled": false,
       "rollout_percentage": 100,
       "feature_state_value": { "type": "string", "value": "control" },
       "multivariate_feature_state_values": [
         { "multivariate_feature_option": <social_proof variation id>, "percentage_allocation": 50 }
       ]
     }
   }
   ```

   `"enabled": false` is required. **Never create the Production experiment with `"enabled": true`.** The
   `rollout_percentage` only describes the split that will apply once the experiment is started.

2. **Check that nothing is live yet.** Read the experiment back
   (`flagsmith api api/v1/environments/<PRODUCTION_ENV_KEY>/experiments/<experiment id>/`) and confirm that it is not
   running and that `experiment_rollout.enabled` is `false`.

3. **Pass every readiness check** in [FINAL_VERIFICATION.md](FINAL_VERIFICATION.md) against the deployed app: the
   Production keys are set (and the Simulation key is not), the deployed commit is the reviewed one, and the flag,
   variation key and metrics match.

4. **Only then start it**, with explicit approval from the person running the experiment:

   ```bash
   # POST api/v1/environments/<PRODUCTION_ENV_KEY>/experiments/<experiment id>/start/
   ```

   Starting marks the experiment as running and is the step that enables the rollout. From this moment real visitors are
   enrolled and every enrolled visitor adds exposures.

`<PRODUCTION_ENV_KEY>` is the environment's client-side key, which is how the API identifies environments. It is not a
secret, but keep it out of chat and commits anyway.

## 7. Attaching the other metrics

The experiments API has a nested metrics endpoint (`api/experimentation/experiment_urls.py`):

```bash
flagsmith api api/v1/environments/<ENV_KEY>/experiment-metrics/          # find the metric ids
flagsmith api api/v1/environments/<ENV_KEY>/experiments/                 # find the experiment id
# For each extra metric, POST to:
#   api/v1/environments/<ENV_KEY>/experiments/<experiment id>/metrics/
#   { "metric": <metric id>, "expected_direction": "increase" }        # Signup click-through
#   { "metric": <metric id>, "expected_direction": "not_increase" }    # Time to signup click
```

Use the Flagsmith CLI (`flagsmith login`, then `flagsmith api …`), or send
`Authorization: Api-Key <organisation API key>` to `https://api.flagsmith.com/`.

Notes:

- The API requires an `expected_direction` even for the Informational metric. The dashboard's results code shows
  Informational metrics as neutral, so the choice does not label that metric a win or a loss.
- Metrics cannot be changed once an experiment is completed.

## 8. Checking that events reach Flagsmith

1. **In the browser:** open the deployed app, then DevTools → Network, filtered to `events.api.flagsmith.com`.
   - Within about a second you should see a `POST /v1/events` containing `$flag_exposure`, answered with a 2xx status.
   - Clicking **Sign Up** sends one `signup_clicked`.
2. **On the server:** a valid demo signup returns **201** from `/api/signup` only after Flagsmith's events API has
   accepted `signed_up`. A **502** means it did not, and the visitor is told to try again.
3. **In Flagsmith:** **Environment Settings › Warehouse** shows the total events rising, and the event names
   `$flag_exposure`, `signup_clicked` and `signed_up`. Processing can lag, especially for the first event.
4. **On the experiment page:** the **Exposures** panel shows visitors per variant. Click **Refresh results**; results
   are recomputed at most every 5 minutes.
   - Each variant shows **Collecting data** until it has 50 identities and, for Occurrence metrics, 5 conversions.
   - If a **sample ratio mismatch** warning appears, do not act on the results.
5. **For the simulator:** its summary prints each event's sent and confirmed counts, and the dataset stores them.

## Self-hosted Flagsmith (not supported by StudyStreak as built)

Flagsmith's documentation describes self-hosted Experimentation:

- set `EXPERIMENTATION_ENABLED=true` on the API;
- store events in the Flagsmith database (PostgreSQL only, evaluation use) or your own warehouse;
- point the SDKs at your API URL and events URL.

StudyStreak does **not** support this today. Both SDKs are created with their default Flagsmith Cloud URLs, and there is
no configuration to change them. The browser's `keepalive` wrapper also matches only the Cloud events URL. Self-hosting
would need small code changes, which have not been made or tested.
