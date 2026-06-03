import { useEffect, useRef, useState } from 'react'
import { useDispatch } from 'react-redux'
import AppActions from 'common/dispatcher/app-actions'
import { getStore } from 'common/store'
import {
  organisationService,
  useGetOrganisationsQuery,
} from 'common/services/useOrganisation'
import {
  projectService,
  useCreateProjectMutation,
} from 'common/services/useProject'
import {
  getEnvironments,
  useCreateEnvironmentMutation,
} from 'common/services/useEnvironment'
import { useCreateProjectFlagMutation } from 'common/services/useProjectFlag'
import useSelectedOrganisation from 'common/hooks/useSelectedOrganisation'
import { useGetProfileQuery } from 'common/services/useProfile'
import { Req } from 'common/types/requests'
import {
  Environment,
  PagedResponse,
  ProjectFlag,
  ProjectSummary,
} from 'common/types/responses'
import { useSmartDefaults } from 'web/components/pages/onboarding-quickstart/hooks/useSmartDefaults'
import { createOrganisationViaAccountStore } from 'web/components/pages/onboarding-quickstart/hooks/createOrganisationViaAccountStore'

const FLAG_NAME = 'show_demo_button'

export type OnboardingResourcesStatus = 'creating' | 'ready' | 'error'

export type OnboardingResources = {
  status: OnboardingResourcesStatus
  organisationId: number | null
  organisationName: string
  projectName: string
  featureName: string
  environment: Environment | null
  environmentKey: string
  projectId: number | null
  error: unknown
}

/**
 * Ensures the single-page flow has something to show, idempotently: on a first
 * visit it creates the org (if needed), a project, Development + Production
 * environments, and a first flag; on a return visit it reuses whatever already
 * exists instead of recreating. Runs once per mount.
 *
 * Idempotency matters because this page can be revisited. Two specific traps it
 * avoids:
 *  - Creating a second organisation. The org is resolved from the loaded
 *    organisations list (not just the legacy AccountStore selection, which may
 *    still be unresolved on a return visit) — creating only when the user has
 *    none. Otherwise plan org caps reject the create with a 403.
 *  - Piling up duplicate "My first project"s. An existing project (and its
 *    environment) is reused; the flag is ensured, tolerating an
 *    already-exists conflict.
 *
 * Waits for the profile + organisations query to settle before deciding
 * reuse-vs-create, so the decision is made against real data.
 */
export const useEnsureOnboardingResources = (): OnboardingResources => {
  const dispatch = useDispatch()
  const { data: profile } = useGetProfileQuery({})
  const { data: organisations, isLoading: orgsLoading } =
    useGetOrganisationsQuery({})
  const defaults = useSmartDefaults(
    profile?.email ?? '',
    profile?.first_name ?? '',
  )
  const selectedOrganisation = useSelectedOrganisation()

  const [createProject] = useCreateProjectMutation()
  const [createEnvironment] = useCreateEnvironmentMutation()
  const [createProjectFlag] = useCreateProjectFlagMutation()

  const [status, setStatus] = useState<OnboardingResourcesStatus>('creating')
  const [environment, setEnvironment] = useState<Environment | null>(null)
  const [environmentKey, setEnvironmentKey] = useState('')
  const [organisationId, setOrganisationId] = useState<number | null>(null)
  const [projectId, setProjectId] = useState<number | null>(null)
  const [organisationName, setOrganisationName] = useState('')
  const [projectName, setProjectName] = useState('')
  const [error, setError] = useState<unknown>(null)
  const ranRef = useRef(false)

  useEffect(() => {
    // Run once, and only after the profile + organisations have loaded so the
    // reuse-vs-create decision is made against real data.
    if (ranRef.current || !profile || orgsLoading) {
      return
    }
    ranRef.current = true

    const run = async () => {
      try {
        // Reuse an existing organisation — the selected one, or the first in
        // the loaded list — and only create when the user has none. This is
        // what prevents a return visit from creating a second org (and hitting
        // the plan's org cap with a 403).
        const existingOrg = selectedOrganisation ?? organisations?.results?.[0]
        let organisationId = existingOrg?.id
        let resolvedOrgName = existingOrg?.name ?? ''

        if (!organisationId) {
          resolvedOrgName = defaults.orgName || 'My organisation'
          organisationId = await createOrganisationViaAccountStore(
            resolvedOrgName,
          )
          AppActions.selectOrganisation(organisationId)
          dispatch(
            organisationService.util.invalidateTags([
              { id: 'LIST', type: 'Organisation' },
            ]),
          )
        }

        // Reuse an existing project, else create one with Dev + Prod
        // environments. Avoids stacking up duplicate projects on revisits.
        const projects = await getStore()
          .dispatch(
            projectService.endpoints.getProjects.initiate({ organisationId }),
          )
          .unwrap()
        let project: ProjectSummary | undefined = projects?.[0]
        if (!project) {
          const projName = defaults.projectName || 'My first project'
          project = await createProject({
            name: projName,
            organisation: organisationId,
          }).unwrap()
          await createEnvironment({
            name: 'Development',
            project: project.id,
          }).unwrap()
          await createEnvironment({
            name: 'Production',
            project: project.id,
          }).unwrap()
        }

        // Surface an environment key — reuse one, preferring Development;
        // create it only if the (reused) project somehow has none.
        const envResult = (await getEnvironments(getStore(), {
          projectId: project.id,
        })) as { data?: PagedResponse<Environment> }
        const environments = envResult?.data?.results ?? []
        let devEnvironment =
          environments.find((env) => env.name === 'Development') ??
          environments[0]
        if (!devEnvironment) {
          devEnvironment = await createEnvironment({
            name: 'Development',
            project: project.id,
          }).unwrap()
        }

        // Ensure the demo flag exists. A unique-name conflict on a revisit is
        // expected and fine — we display the flag either way.
        try {
          const featureBody: Partial<ProjectFlag> = {
            name: FLAG_NAME,
            project: project.id,
            type: 'STANDARD',
          }
          await createProjectFlag({
            body: featureBody as Req['createProjectFlag']['body'],
            project_id: project.id,
          }).unwrap()
        } catch {
          // Flag already exists in this project — reuse it.
        }

        // Refresh the legacy org store so the shell sees the project.
        AppActions.refreshOrganisation()

        setOrganisationId(organisationId)
        setOrganisationName(resolvedOrgName)
        setProjectName(project.name)
        setProjectId(project.id)
        setEnvironment(devEnvironment)
        setEnvironmentKey(devEnvironment.api_key)
        setStatus('ready')
      } catch (e) {
        setError(e)
        setStatus('error')
      }
    }
    run()
  }, [
    profile,
    orgsLoading,
    organisations,
    selectedOrganisation,
    defaults,
    dispatch,
    createProject,
    createEnvironment,
    createProjectFlag,
  ])

  return {
    environment,
    environmentKey,
    error,
    featureName: FLAG_NAME,
    organisationId,
    organisationName,
    projectId,
    projectName,
    status,
  }
}
