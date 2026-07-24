# Removing the `InputGroup` `component` prop

Plan to retire `<InputGroup component={...} />` in favour of purpose-built, accessible field components. Contributes to #7364 (unified form field standardisation).

## Why

`InputGroup`'s value is that it wires a labelled field's accessibility for you: `htmlFor` / `id` on the label and control, `aria-invalid`, and `aria-describedby` to the error, all off one id.

The `component` prop bypasses all of that. When you pass `component={<Select .../>}`:

- the label renders `htmlFor={id}`, but the custom control never receives that `id`, so the label points at nothing;
- the control gets no `aria-invalid` and no link to the error;
- `FieldError` renders with an id nothing references.

So the field looks wired up and announces none of it to assistive tech. You can see this today in `CreatePipelineStage.tsx`: the "No environments with feature versioning enabled" error is passed via `inputProps.error`, renders as text, and the Select neither references it nor is marked invalid (the red border is hand-drawn via react-select `styles`).

The `component` payload is overwhelmingly a `Select`. A generic `children` + `cloneElement` fix would not help, because react-select needs its a11y threaded through its own props (`inputId`, `aria-*`), not an `id` on a wrapper. That is why the fix is a purpose-built component, not a tweak to `InputGroup`.

## End state

| Case | Replacement |
| --- | --- |
| `InputGroup` wrapping a `Select` | `SelectField` (label + Select + FieldError, a11y wired via `inputId`) |
| `InputGroup` wrapping a genuinely custom control (colour picker, DateSelect, bespoke widget) | standalone `FieldLabel` + `FieldError`, wiring the id trio by hand |
| Plain text / number / textarea | `InputGroup` (unchanged) |

Then the `component` prop is deleted from `InputGroup`, and a lint rule stops it coming back.

## Inventory (origin/main)

~21 files use `<InputGroup component={...} />`. Bucketed by payload:

**Select (migrate to `SelectField`)**
- `web/components/tables/TableValueFilter.tsx`
- `web/components/release-pipelines/CreatePipelineStage.tsx` (Environment, Trigger)
- `web/components/release-pipelines/SinglePipelineStageAction.tsx` (Flag Action, Segment)
- `web/components/release-pipelines/AddToReleasePipelineModal.tsx`
- `web/components/modals/CreateMetadataField.tsx` (Type)
- `web/components/modals/CreateSegmentUsersTabContent.tsx` (Environment)
- `web/components/modals/CreateSegment.tsx`
- `web/components/modals/create-feature/tabs/FeatureValueTab.tsx`
- `web/components/modals/create-feature/tabs/FeatureSettingsTab.tsx`
- `web/components/mv/VariationValueInput/VariationValueInput.tsx`
- `web/components/pages/CreateOrganisationPage.tsx`
- `web/components/pages/CreateEnvironmentPage.tsx` (x2)
- `web/components/pages/ChangeRequestDetailPage.tsx`
- `web/components/pages/ReleaseManagerPage.tsx`
- `web/components/pages/environment-settings/EnvironmentSettingsPage.tsx`
- `web/components/pages/organisation-settings/tabs/sso/saml/modals/CreateSAML.tsx` (x2)
- `web/components/pages/organisation-settings/tabs/sso/scim/modals/ScimTokenModal.tsx`
- `web/components/pages/project-settings/tabs/general-tab/sections/additional-settings/FeatureNameValidation.tsx`
- `web/components/metadata/SupportedContentTypesSelect.tsx`
- `web/components/EditPermissions.tsx`

**Non-Select (migrate to standalone `FieldLabel` + `FieldError`)**
- `web/components/modals/ChangeRequestModal.tsx` (datepicker; check both sites)
- `web/components/tags/CreateEditTag.tsx` (colour picker)

Counts are a starting map, not a per-site read. A few `component=` matches in these files may not be on `InputGroup`; confirm per site when migrating.

## Steps

1. **Ship `SelectField`** (this PR): label + Select + FieldError, a11y wired via `inputId` / `aria-*`, plus a Storybook story. No call sites migrated yet.
2. **Verify the a11y forwarding** through react-select v5 (that `aria-errormessage` / `aria-invalid` reach the input; fall back to `aria-describedby` if not). Add a visual error state (red border) inside `SelectField` so consumers stop hand-rolling `styles`.
3. **Migrate the Select sites** to `SelectField` in small batches by area (release-pipelines, modals, settings). Each batch is its own PR.
4. **Migrate the non-Select sites** to standalone `FieldLabel` + `FieldError`.
5. **Delete `component` from `InputGroup`** and land a lint guardrail (`no-restricted-syntax` on a `component` attribute on `<InputGroup>`) in the same PR, so the door shuts behind the migration.

## Notes

- `SelectField` is a first cut. The error-state styling and the react-select aria verification (step 2) are deliberately follow-ups so this PR stays reviewable.
- The base `Select` (`web/project/project-components.js`) is untyped JS and spreads props into react-select, which is why `SelectField` types its own surface off react-select's `Props` plus the base's custom extras (`size`, `autoSelect`).

## Related follow-up: drop the Select E2E fork (separate PR, after SelectField)

The base `Select` swaps to a bespoke `<input> + <a>` DOM when `global.E2E` is true. This is TestCafe-era scaffolding; E2E is fully Playwright now, and Playwright can drive real react-select. The fork is the source of the "Select behaves differently under E2E" bugs (e.g. the fork keys its input off `id`, while react-select uses `inputId`).

Kept out of the `component`-prop migration on purpose. Sequenced **after** the Select call sites move to `SelectField`, as its own Select-only PR.

Prefer accessibility selectors over `data-test`. This is the payoff of `SelectField`: a select with a proper label gets an accessible name, so Playwright can target it by role, with no bespoke test id. The sequencing matters here, once the target selects render through `SelectField` (with a `title`), the role selectors work.

This also makes the E2E suite a standing accessibility guard: a role/name selector only resolves if the component is genuinely accessible, so if a select later loses its label the test fails loudly instead of the accessibility silently rotting. `data-test` selectors give no such signal.

1. Add a Playwright `selectOption(name, optionLabel)` helper using role/name selectors:
   ```ts
   await page.getByRole('combobox', { name }).click()          // open the menu
   await page.getByRole('option', { name: optionLabel }).click()
   ```
2. Migrate the sites that use the fork's `*-option-N` ids to the helper: `invite-test.pw.ts`, `roles-test.pw.ts`, and the `select-segment-option-${i}` helper in `e2e-helpers.playwright.ts`.
3. Remove the `E2E ?` branch from `Select`.
4. Run the affected specs (`invite`, `roles`, segment) to confirm. Requires Docker + API on localhost:8000.

Fallback: a select without a visible label (inline filters, etc.) has no accessible name. Give it an `aria-label` (via `SelectField`) so it stays role-targetable, rather than reintroducing a `data-test`.

Scope is `Select` only. The other E2E forks (`toast`, `ValueEditor`, `FeatureAction`, `ActionItem`, the config/organisation stores) are out of scope.
