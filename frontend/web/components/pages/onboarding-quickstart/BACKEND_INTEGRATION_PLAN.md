# Onboarding quickstart — backend integration plan

> Wiring the flow's create chain to real APIs. Step 5 (first-eval
> signal) stays mocked via `useFirstEvaluationPoll` — out of scope here.
> Companion to `PLAN.md` and `FIRST_EVAL_BACKEND_PLAN.md`.

## Decisions (locked)

- **New RTK Query mutations**, not the legacy Flux actions. Aligns with
  the migrate-off-`AccountStore`/`OrganisationStore` direction.
- **Two default environments** (Development + Production) per project,
  matching what normal project creation produces. Onboarding lands on
  Development.

## The create chain (`handleFinish`)

```
createOrganisation({ name })            → org.id        (skip if org exists)
  → createProject({ name, organisation: org.id })       → project.id
    → createEnvironment({ name: 'Development', project }) → env.api_key
    → createEnvironment({ name: 'Production',  project })
    → createProjectFlag({ project_id, body })            (already wired)
  → navigate /project/{project.id}/environment/{dev.api_key}/features
```

Each step `.unwrap()`'d so a rejection stops the chain and surfaces an error.

## Phases

### Phase 1 — RTK mutations (low risk)
- `requests.ts`: add `createOrganisation`, `createProject`,
  `createEnvironment` request types.
- `useOrganisation.ts`: `createOrganisation` mutation, invalidates
  `Organisation/LIST`, returns `Res['organisation']`.
- `useProject.ts`: `createProject` mutation, invalidates `Project/LIST`,
  returns `Res['project']`.
- `useEnvironment.ts`: `createEnvironment` mutation, invalidates
  `Environment/LIST`, returns `Res['environment']`.
- Export the three `useCreate…Mutation` hooks.

### Phase 2 — Chain in `handleFinish`
- Replace the `DEMO_ENVIRONMENT_KEY` stub with the awaited chain.
- Fix the features URL: route needs **numeric `project.id`** and the
  Development **`api_key`** — today it wrongly uses `projectName` as the
  path slug (Matt's Step 5 "Explore the dashboard" bug traces here).
- Reuse the create-feature modal's body shape for `createProjectFlag`
  (name, type, default values).

### Phase 3 — Flux coherence (the real risk)
The org switcher, project list, and downstream context read from the
**Flux** `AccountStore`/`OrganisationStore`. Entities created purely via
RTK are invisible to them until refresh. After the chain succeeds, call
`AppActions.refreshOrganisation()` (what Flux `createProject` already
does) so the new org/project appear app-wide. Verify the switcher and
project list reflect the new entities without a hard reload.

### Phase 4 — Branching + guards
- **Org may already exist**: post-signup `register()` auto-creates an org
  when `organisation_name` was given. If an org exists, skip the org
  step / reuse it rather than creating a duplicate.
- **Idempotency**: going Back and re-submitting must not create a second
  org/project. Store created ids in state; on re-submit, reuse them.
- **Errors**: per-step failure handling (duplicate name, permissions,
  self-hosted org-creation restrictions). None today.

### Phase 5 — Flag + cleanup
- Revert `GettingStartedSwitch` `FORCE_ON = true` to the real
  `Utils.getFlagsmithHasFeature('onboarding_quickstart_flow')` gate.

## Out of scope
- First-eval signal (stays mocked — see `FIRST_EVAL_BACKEND_PLAN.md`).
- PM "Connect your tools" integrations destination (product decision).
- Plan-based "Invite a teammate" gating (needs subscription context).

## Estimate
~3 dev-days: Phase 1–2 ≈ 1 day; Phases 3–4 (coherence, org-exists,
guards/errors) ≈ 2 days.
