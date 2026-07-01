import AppActions from 'common/dispatcher/app-actions'
import { getStore } from 'common/store'
import { organisationService } from 'common/services/useOrganisation'
import { projectService } from 'common/services/useProject'
import {
  environmentService,
  getEnvironments,
} from 'common/services/useEnvironment'
import { projectFlagService } from 'common/services/useProjectFlag'
import { Req } from 'common/types/requests'
import {
  Environment,
  PagedResponse,
  ProjectSummary,
} from 'common/types/responses'
import { SmartDefaults } from './useSmartDefaults'
import { createOrganisationViaAccountStore } from './createOrganisationViaAccountStore'

type Store = ReturnType<typeof getStore>

const FLAG_NAME = 'show_demo_button'
const DEFAULT_ORG_NAME = 'My organisation'
const DEFAULT_PROJECT_NAME = 'My first project'
// Written on create and matched by name on reuse, so the two must stay in step.
const DEV_ENVIRONMENT_NAME = 'Development'
const PROD_ENVIRONMENT_NAME = 'Production'

type ExistingOrg = { id: number; name: string }

export type BootstrapInput = {
  defaults: SmartDefaults
  existingOrg?: ExistingOrg
}

export type OnboardingBootstrap = {
  organisationId: number
  organisationName: string
  project: ProjectSummary
  environment: Environment
  featureName: string
}

// Reuse the loaded org, or create one only when the user has none (the plan
// org cap rejects extra creates with a 403). Create goes through the legacy
// AccountStore so the shell's current-org selection is populated.
async function ensureOrganisation(
  store: Store,
  { defaults, existingOrg }: BootstrapInput,
): Promise<ExistingOrg> {
  if (existingOrg) {
    return existingOrg
  }
  const name = defaults.orgName || DEFAULT_ORG_NAME
  const id = await createOrganisationViaAccountStore(name)
  AppActions.selectOrganisation(id)
  store.dispatch(
    organisationService.util.invalidateTags([
      { id: 'LIST', type: 'Organisation' },
    ]),
  )
  return { id, name }
}

// Reuse the first project, else create one with Development + Production
// environments. Avoids stacking up duplicate projects on revisits.
async function ensureProject(
  store: Store,
  organisationId: number,
  defaults: SmartDefaults,
): Promise<ProjectSummary> {
  const projects = await store
    .dispatch(projectService.endpoints.getProjects.initiate({ organisationId }))
    .unwrap()
  const existing = projects?.[0]
  if (existing) {
    return existing
  }
  const project = await store
    .dispatch(
      projectService.endpoints.createProject.initiate({
        name: defaults.projectName || DEFAULT_PROJECT_NAME,
        organisation: organisationId,
      }),
    )
    .unwrap()
  await store
    .dispatch(
      environmentService.endpoints.createEnvironment.initiate({
        name: DEV_ENVIRONMENT_NAME,
        project: project.id,
      }),
    )
    .unwrap()
  await store
    .dispatch(
      environmentService.endpoints.createEnvironment.initiate({
        name: PROD_ENVIRONMENT_NAME,
        project: project.id,
      }),
    )
    .unwrap()
  return project
}

// Surface an environment key: reuse one (preferring Development), or create it
// only if the reused project somehow has none.
async function ensureEnvironments(
  store: Store,
  project: ProjectSummary,
): Promise<Environment> {
  const envResult = (await getEnvironments(store, {
    projectId: project.id,
  })) as { data?: PagedResponse<Environment> }
  const environments = envResult?.data?.results ?? []
  const devEnvironment =
    environments.find((env) => env.name === DEV_ENVIRONMENT_NAME) ??
    environments[0]
  if (devEnvironment) {
    return devEnvironment
  }
  return store
    .dispatch(
      environmentService.endpoints.createEnvironment.initiate({
        name: DEV_ENVIRONMENT_NAME,
        project: project.id,
      }),
    )
    .unwrap()
}

// Reuse the project's existing flag (keeps a renamed flag and stops piling up
// duplicates on revisit); only create the demo flag when there are none.
// Returns the real flag name so the header shows what's actually there.
async function ensureFlag(
  store: Store,
  project: ProjectSummary,
): Promise<string> {
  const flags = await store
    .dispatch(
      projectFlagService.endpoints.getProjectFlags.initiate({
        project: `${project.id}`,
      }),
    )
    .unwrap()
  const existing = flags?.results?.[0]
  if (existing) {
    return existing.name
  }
  const created = await store
    .dispatch(
      projectFlagService.endpoints.createProjectFlag.initiate({
        body: {
          name: FLAG_NAME,
          project: project.id,
          type: 'STANDARD',
        } as Req['createProjectFlag']['body'],
        project_id: project.id,
      }),
    )
    .unwrap()
  return created?.name ?? FLAG_NAME
}

// Idempotently bring up everything the single-page flow needs: org, project,
// Development + Production environments, and a first flag, reusing whatever
// already exists. Split into ensure* steps so each concern is testable and the
// reuse-vs-create decisions are obvious.
export async function bootstrapOnboarding(
  store: Store,
  input: BootstrapInput,
): Promise<OnboardingBootstrap> {
  const organisation = await ensureOrganisation(store, input)
  const project = await ensureProject(store, organisation.id, input.defaults)
  const environment = await ensureEnvironments(store, project)
  const featureName = await ensureFlag(store, project)
  // Refresh the legacy org store so the shell sees the project.
  AppActions.refreshOrganisation()
  return {
    environment,
    featureName,
    organisationId: organisation.id,
    organisationName: organisation.name,
    project,
  }
}
