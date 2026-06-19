import { useEffect, useRef, useState } from 'react'
import { getStore } from 'common/store'
import { useGetOrganisationsQuery } from 'common/services/useOrganisation'
import useSelectedOrganisation from 'common/hooks/useSelectedOrganisation'
import { useGetProfileQuery } from 'common/services/useProfile'
import { Environment } from 'common/types/responses'
import { useSmartDefaults } from './useSmartDefaults'
import { bootstrapOnboarding } from './bootstrapOnboarding'

export type OnboardingResourcesStatus = 'creating' | 'ready' | 'error'

export type OnboardingResources = {
  status: OnboardingResourcesStatus
  organisationId: number | null
  organisationName: string
  projectName: string
  featureName: string
  caseSensitive: boolean
  environment: Environment | null
  environmentKey: string
  projectId: number | null
  error: unknown
}

/**
 * Drives the single-page flow's resources: waits for the profile + organisations
 * to load, then runs bootstrapOnboarding once to reuse-or-create the org,
 * project, environments and first flag. The imperative orchestration lives in
 * bootstrapOnboarding; this hook just owns the React state and run-once guard.
 */
export const useEnsureOnboardingResources = (): OnboardingResources => {
  const { data: profile } = useGetProfileQuery({})
  const { data: organisations, isLoading: orgsLoading } =
    useGetOrganisationsQuery({})
  const defaults = useSmartDefaults(
    profile?.email ?? '',
    profile?.first_name ?? '',
  )
  const selectedOrganisation = useSelectedOrganisation()

  const [status, setStatus] = useState<OnboardingResourcesStatus>('creating')
  const [environment, setEnvironment] = useState<Environment | null>(null)
  const [environmentKey, setEnvironmentKey] = useState('')
  const [organisationId, setOrganisationId] = useState<number | null>(null)
  const [projectId, setProjectId] = useState<number | null>(null)
  const [organisationName, setOrganisationName] = useState('')
  const [projectName, setProjectName] = useState('')
  const [featureName, setFeatureName] = useState('')
  // Whether the project enforces lower-case feature names; drives the same name
  // normalisation the create-feature modal applies (see the header).
  const [caseSensitive, setCaseSensitive] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const ranRef = useRef(false)

  useEffect(() => {
    // Run once, and only after the profile + organisations have loaded so the
    // reuse-vs-create decision is made against real data.
    if (ranRef.current || !profile || orgsLoading) {
      return
    }
    ranRef.current = true

    // Reuse the selected org, or the first loaded; bootstrapOnboarding creates
    // one only when there's none.
    const existing = selectedOrganisation ?? organisations?.results?.[0]
    const existingOrg = existing
      ? { id: existing.id, name: existing.name }
      : undefined

    bootstrapOnboarding(getStore(), { defaults, existingOrg })
      .then((res) => {
        setOrganisationId(res.organisationId)
        setOrganisationName(res.organisationName)
        setProjectName(res.project.name)
        setProjectId(res.project.id)
        setCaseSensitive(!!res.project.only_allow_lower_case_feature_names)
        setEnvironment(res.environment)
        setEnvironmentKey(res.environment.api_key)
        setFeatureName(res.featureName)
        setStatus('ready')
      })
      .catch((e) => {
        setError(e)
        setStatus('error')
      })
  }, [profile, orgsLoading, organisations, selectedOrganisation, defaults])

  return {
    caseSensitive,
    environment,
    environmentKey,
    error,
    featureName,
    organisationId,
    organisationName,
    projectId,
    projectName,
    status,
  }
}
