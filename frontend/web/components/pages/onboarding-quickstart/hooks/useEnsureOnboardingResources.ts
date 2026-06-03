import { useEffect, useRef, useState } from 'react'
import { useDispatch } from 'react-redux'
import AppActions from 'common/dispatcher/app-actions'
import {
  organisationService,
  useGetOrganisationsQuery,
} from 'common/services/useOrganisation'
import { useCreateProjectMutation } from 'common/services/useProject'
import { useCreateEnvironmentMutation } from 'common/services/useEnvironment'
import { useCreateProjectFlagMutation } from 'common/services/useProjectFlag'
import useSelectedOrganisation from 'common/hooks/useSelectedOrganisation'
import { useGetProfileQuery } from 'common/services/useProfile'
import { Req } from 'common/types/requests'
import { ProjectFlag } from 'common/types/responses'
import { useSmartDefaults } from 'web/components/pages/onboarding-quickstart/hooks/useSmartDefaults'
import { createOrganisationViaAccountStore } from 'web/components/pages/onboarding-quickstart/hooks/createOrganisationViaAccountStore'

const FLAG_NAME = 'show_demo_button'

export type OnboardingResourcesStatus = 'creating' | 'ready' | 'error'

export type OnboardingResources = {
  status: OnboardingResourcesStatus
  organisationName: string
  projectName: string
  featureName: string
  environmentKey: string
  projectId: number | null
  error: unknown
}

/**
 * Ensures the single-page flow has something to show: reuses the selected
 * organisation (the common case after signup) or creates one, then creates a
 * project, Development + Production environments, and a first flag — the same
 * chain the stepped flow runs on finish, but here on entry. Runs once.
 *
 * Waits for the organisations query to settle before deciding reuse-vs-create,
 * so we don't create a duplicate org while the list is still loading.
 */
export const useEnsureOnboardingResources = (): OnboardingResources => {
  const dispatch = useDispatch()
  const { data: profile } = useGetProfileQuery({})
  const { isLoading: orgsLoading } = useGetOrganisationsQuery({})
  const defaults = useSmartDefaults(
    profile?.email ?? '',
    profile?.first_name ?? '',
  )
  const selectedOrganisation = useSelectedOrganisation()

  const [createProject] = useCreateProjectMutation()
  const [createEnvironment] = useCreateEnvironmentMutation()
  const [createProjectFlag] = useCreateProjectFlagMutation()

  const [status, setStatus] = useState<OnboardingResourcesStatus>('creating')
  const [environmentKey, setEnvironmentKey] = useState('')
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
        const orgName =
          selectedOrganisation?.name || defaults.orgName || 'My organisation'
        const projName = defaults.projectName || 'My first project'

        let organisationId = selectedOrganisation?.id
        if (!organisationId) {
          organisationId = await createOrganisationViaAccountStore(orgName)
          AppActions.selectOrganisation(organisationId)
          dispatch(
            organisationService.util.invalidateTags([
              { id: 'LIST', type: 'Organisation' },
            ]),
          )
        }

        const project = await createProject({
          name: projName,
          organisation: organisationId,
        }).unwrap()

        const devEnvironment = await createEnvironment({
          name: 'Development',
          project: project.id,
        }).unwrap()
        await createEnvironment({
          name: 'Production',
          project: project.id,
        }).unwrap()

        const featureBody: Partial<ProjectFlag> = {
          name: FLAG_NAME,
          project: project.id,
          type: 'STANDARD',
        }
        await createProjectFlag({
          body: featureBody as Req['createProjectFlag']['body'],
          project_id: project.id,
        }).unwrap()

        // Refresh the legacy org store so the shell sees the new project.
        AppActions.refreshOrganisation()

        setOrganisationName(orgName)
        setProjectName(projName)
        setProjectId(project.id)
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
    selectedOrganisation,
    defaults,
    dispatch,
    createProject,
    createEnvironment,
    createProjectFlag,
  ])

  return {
    environmentKey,
    error,
    featureName: FLAG_NAME,
    organisationName,
    projectId,
    projectName,
    status,
  }
}
