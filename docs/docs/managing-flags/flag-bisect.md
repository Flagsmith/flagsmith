---
title: Flag Bisect
sidebar_label: Flag Bisect
sidebar_position: 5
---

When errors rise shortly after several flags changed, Flag Bisect finds which change caused it without rolling all of
them back. It reverts a subset of the recent changes for a small, randomised canary segment, compares that segment with
everyone else, and repeats until one change (or a pair that only breaks together) explains the regression. A person
approves before anything changes, and restoring the culprit for everyone needs a second person.

Flag Bisect is turned off by default. Set `FLAG_BISECT_ENABLED=true` on the API and the task processor to turn it on.

## How it works

1. **Your servers report outcomes.** Send whether each request succeeded, with the identity it was served for, to
   `POST /api/v1/flag-bisect/signals/` using a server-side environment key.
2. **An incident opens.** When the failure rate shifts, Flag Bisect dates the onset and lists every change to an
   environment default in the two hours before it, from Flagsmith's own history (feature versions with versioning on, or
   the flag's history records without it).
3. **An environment admin approves the envelope.** The envelope sets the canary size (1 to 20% of identities), the
   maximum number of rounds and minutes. Flag Bisect proposes the smallest canary that should decide each probe within
   about five minutes, from the traffic since the onset and the size of the regression, and says how long a probe should
   take, or warns when traffic is too low for any size. Nothing changes in Flagsmith until the envelope is approved.
4. **Probes.** Each round reverts some of the changes for the canary segment only, through segment overrides. Everyone
   else keeps today's flags. After 30 seconds, outcomes are counted separately for identities inside and outside the
   segment, using the same percentage split the SDKs evaluate. A sequential test decides whether the canary healed.
5. **Confirmation.** Before anyone acts, one more probe reverts only the suspected culprit.
6. **Remediation.** One person proposes restoring the culprit for everyone and a different person approves it. Flag
   Bisect writes the environment default and reads it back. Other changes stay as they are.

The canary is a system segment named `flag-bisect-<incident>-canary`. It is deleted when the incident ends.

## Reporting outcomes

Flag Bisect needs to know, for each identity, whether its requests succeed. Choose one of two ways.

### From Experimentation events

If your apps already send [Experimentation](/experimentation) events to
[Flagsmith's own database](/experimentation/self-hosting#flagsmith-database), nothing else is needed. On the Flag Bisect
page, name one event that means a request failed (for example `checkout_failed`) and one that means it succeeded (for
example `checkout_completed`). Each swarm pass reads the new events, dates them by when they happened, and counts them
for the identity they were sent for. A new source reads back no further than 45 minutes.

The same setting is available at `PUT /api/v1/environments/<environment_api_key>/flag-bisect/signal-source/` with
`failure_event` and `success_event`.

### From your servers

```bash
curl -X POST https://<your-flagsmith>/api/v1/flag-bisect/signals/ \
  -H "X-Environment-Key: ser.<server-key>" \
  -H "Content-Type: application/json" \
  -d '{"signals": [{"identifier": "user-42", "ok": false}, {"identifier": "user-43", "ok": true}]}'
```

Send up to 1,000 outcomes per request. Use the same identifier you pass to the SDK, so the canary is matched exactly.

## API

Under `/api/v1/environments/<environment_api_key>/flag-bisect/incidents/`, for environment admins:

| Method and path                   | Purpose                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------ |
| `GET /`                           | Incidents, newest first                                                                    |
| `GET /<id>/`                      | Suspects with prior and posterior odds, probes, leading explanations and the agents' trail |
| `POST /<id>/approve-envelope/`    | Approve the envelope; optional `canary_percent`, `max_rounds`, `max_minutes`               |
| `POST /<id>/abort/`               | Stop and remove the canary; `reason` required                                              |
| `POST /<id>/propose-remediation/` | Propose restoring the culprit for everyone                                                 |
| `POST /<id>/approve-remediation/` | Approve it, as a different user or API key                                                 |

Every action is recorded in the audit log.

## Things to know

- With change requests enabled for the environment, Flag Bisect refuses to change flags.
- Flags in a running or paused experiment are left alone, so the swarm never competes with an experiment's rollout.
  Pause or complete the experiment to include them.
- Identity overrides take precedence over the canary's segment overrides.
- It needs traffic: the smaller the regression, the more requests each probe needs.
- It handles one culprit or a pair of changes that only fail together. Three or more interacting changes end as
  inconclusive.
- The swarm runs as the recurring task `run_flag_bisect_swarm` every 30 seconds. Like any recurring task, the task
  processor disables it after four consecutive failures (for example, while the database refuses connections), and no
  new incidents open until it is enabled again.
- A probe can be wrong (each has a nominal 5% error rate), which is why the confirmation probe runs before anyone acts.
