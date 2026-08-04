import AppActions from 'common/dispatcher/app-actions'
import { getStore } from 'common/store'
import { organisationService } from 'common/services/useOrganisation'
import { projectService } from 'common/services/useProject'
import {
  environmentService,
  getEnvironments,
} from 'common/services/useEnvironment'
import { projectFlagService } from 'common/services/useProjectFlag'
import { tagService } from 'common/services/useTag'
import { Req } from 'common/types/requests'
import {
  Environment,
  PagedResponse,
  ProjectFlag,
  ProjectSummary,
  Tag,
} from 'common/types/responses'
import { SmartDefaults } from './useSmartDefaults'
import { createOrganisationViaAccountStore } from './createOrganisationViaAccountStore'
import API from 'project/api'
import Constants from 'common/constants'

type Store = ReturnType<typeof getStore>

const FLAG_NAME = 'show_demo_button'
const DEFAULT_ORG_NAME = 'My organisation'
const DEFAULT_PROJECT_NAME = 'My first project'
const DEV_ENVIRONMENT_NAME = 'Development'
const PROD_ENVIRONMENT_NAME = 'Production'
const ONBOARDING_TAG = {
  color: '#3cb371',
  description: 'Created during onboarding',
  label: 'Onboarding',
}

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

async function ensureOrganisation(
  store: Store,
  { defaults, existingOrg }: BootstrapInput,
): Promise<ExistingOrg> {
  // Create only when the user has none: the plan org cap rejects extra creates
  // with a 403. Goes through AccountStore so the shell adopts the new org.
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
  API.trackEvent(Constants.events.CREATE_FIRST_PROJECT)
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

async function findOnboardingTag(
  store: Store,
  projectId: number,
): Promise<Tag | undefined> {
  const tags = await store
    .dispatch(tagService.endpoints.getTags.initiate({ projectId }))
    .unwrap()
  return tags?.find((t) => t.label === ONBOARDING_TAG.label)
}

async function ensureFlag(
  store: Store,
  project: ProjectSummary,
): Promise<ProjectFlag | undefined> {
  const flags = await store
    .dispatch(
      projectFlagService.endpoints.getProjectFlags.initiate({
        project: `${project.id}`,
      }),
    )
    .unwrap()
  const onboardingTag = await findOnboardingTag(store, project.id)
  const existing =
    (onboardingTag &&
      flags?.results?.find((f) => f.tags?.includes(onboardingTag.id))) ||
    flags?.results?.find((f) => f.name === FLAG_NAME)
  if (existing) {
    return existing
  }
  const isFirstFeature = !flags?.results?.length
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
  if (isFirstFeature) {
    API.trackEvent(Constants.events.CREATE_FIRST_FEATURE)
  }
  return created
}

async function ensureOnboardingTag(
  store: Store,
  project: ProjectSummary,
  flag: ProjectFlag,
): Promise<void> {
  try {
    const tag =
      (await findOnboardingTag(store, project.id)) ??
      (await store
        .dispatch(
          tagService.endpoints.createTag.initiate({
            projectId: project.id,
            tag: ONBOARDING_TAG,
          }),
        )
        .unwrap())
    if (tag && !flag.tags?.includes(tag.id)) {
      await store
        .dispatch(
          projectFlagService.endpoints.updateProjectFlag.initiate({
            body: { ...flag, tags: [...(flag.tags ?? []), tag.id] },
            feature_id: flag.id,
            project_id: project.id,
          }),
        )
        .unwrap()
    }
  } catch {
    // Cosmetic: tagging must never block onboarding.
  }
}

export async function bootstrapOnboarding(
  store: Store,
  input: BootstrapInput,
): Promise<OnboardingBootstrap> {
  const organisation = await ensureOrganisation(store, input)
  const project = await ensureProject(store, organisation.id, input.defaults)
  const environment = await ensureEnvironments(store, project)
  const flag = await ensureFlag(store, project)
  if (flag) {
    await ensureOnboardingTag(store, project, flag)
  }
  AppActions.refreshOrganisation()
  return {
    environment,
    featureName: flag?.name ?? FLAG_NAME,
    organisationId: organisation.id,
    organisationName: organisation.name,
    project,
  }
}
