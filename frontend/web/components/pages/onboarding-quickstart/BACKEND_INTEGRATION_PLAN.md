# Onboarding quickstart — backend integration plan

> Wiring the flow's create chain to real APIs. Step 5 (first-eval
> signal) stays mocked via `useFirstEvaluationPoll` — out of scope here.
> Companion to `PLAN.md` and `FIRST_EVAL_BACKEND_PLAN.md`.

## Decisions (locked)

- **New RTK Query mutations** for project / environment / feature, not the
  legacy Flux actions. Aligns with the migrate-off-`AccountStore`/
  `OrganisationStore` direction.
- **Organisation is hybrid**: reuse the already-selected org (the common
  case — self-serve signup creates + selects one at registration) and skip
  the org step; only create one when none exists. Org *selection* state is
  Flux/Redux-owned (`selectedOrganisation` slice), so a pure-RTK create
  would leave the shell unaware of the new org. The no-org create path uses
  the awaitable RTK `createOrganisation` mutation + `setSelectedOrganisationId`
  (cleaner than the fire-and-forget `AppActions.createOrganisation`, which
  returns no id).
- **Two default environments** (Development + Production) per project,
  matching what normal project creation produces. Onboarding lands on
  Development. Sample identities (created by the Flux flow) are omitted —
  not needed to get a flag working.

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

### Phase 1 — RTK mutations (low risk) — DONE
- `requests.ts`: add `createOrganisation`, `createProject`,
  `createEnvironment` request types.
- `useOrganisation.ts`: `createOrganisation` mutation, invalidates
  `Organisation/LIST`, returns `Res['organisation']`.
- `useProject.ts`: `createProject` mutation, invalidates `Project/LIST`,
  returns `Res['project']`.
- `useEnvironment.ts`: `createEnvironment` mutation, invalidates
  `Environment/LIST`, returns `Res['environment']`.
- Export the three `useCreate…Mutation` hooks.

### Phase 2 — Chain in `handleFinish` — DONE
- Replaced the `DEMO_ENVIRONMENT_KEY` stub with the awaited chain
  (org-reuse-or-create → project → Dev + Prod envs → feature flag).
- Fixed the features URL: now uses **numeric `project.id`** and the
  Development **`api_key`** (Matt's Step 5 "Explore the dashboard" bug).
- Minimal `createProjectFlag` body (`name`, `project`, `type: STANDARD`),
  asserted to the request type.
- Per-step error handling via try/catch → `<ErrorMessage>` on the feature
  step; failures stop the chain.
- Absorbed the org-exists branch (was Phase 4): org step is dropped from
  the timeline when an org is already selected; navigation is array-driven
  so it stays correct.

### Phase 3 — Flux coherence (partially done; needs runtime verification)
After the chain, `AppActions.refreshOrganisation()` is called so the
legacy `OrganisationStore` project list/switcher pick up the new project.
**Still to verify by running the app**: that the switcher + project list
reflect the new entities without a hard reload, and that the no-org create
path (RTK `createOrganisation` + `setSelectedOrganisationId`) leaves any
legacy `AccountStore`-reading surfaces coherent.

### Phase 4 — Remaining guards
- **Idempotency**: going Back after a *partial* failure and re-submitting
  can still create a second project/env. Store created ids in state and
  reuse on retry. (Double-submit during a run is already blocked by
  `isSubmitting`.)
- **Self-hosted / permissions**: org creation may be restricted; surface a
  clear message rather than a raw error.

### Phase 5 — Flag + cleanup — DONE (flag must exist on FoF)
- `GettingStartedSwitch` now gates on
  `Utils.getFlagsmithHasFeature('onboarding_quickstart_flow')` — the
  `FORCE_ON` override is removed. The no-org post-signup routing
  (`App.js`) gates on the same flag.
- **Still required:** create + enable `onboarding_quickstart_flow` on
  Flagsmith-on-Flagsmith. Until it exists, the flag reads false and the
  old `GettingStartedPage` + `/create` flow render (safe default).

### Known follow-ups (not blockers for a flagged rollout)
- No-org users landing on `/getting-started` trigger the shell's
  `OrganisationStore.getOrganisation()` bootstrap with no org id, firing
  harmless failed calls (`get-subscription-metadata` etc.). Dev-only red
  overlay; silent in production. Fix would guard the shared store.

## Out of scope
- First-eval signal (stays mocked — see `FIRST_EVAL_BACKEND_PLAN.md`).
- PM "Connect your tools" integrations destination (product decision).
- Plan-based "Invite a teammate" gating (needs subscription context).

## Estimate
~3 dev-days: Phase 1–2 ≈ 1 day; Phases 3–4 (coherence, org-exists,
guards/errors) ≈ 2 days.
