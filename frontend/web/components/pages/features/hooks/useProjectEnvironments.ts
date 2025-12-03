import { useCallback, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetProjectQuery } from 'common/services/useProject'
import type { Environment, Project } from 'common/types/responses'

/**
 * Custom hook for fetching and managing project and environment data.
 *
 * Provides both raw data and convenient accessor functions for:
 * - Looking up environments by API key
 * - Accessing project feature limits
 * - Unified loading/error states
 *
 * @param projectId - The project ID to fetch data for
 * @returns Object containing project data, environments, and accessor functions
 *
 * @example
 * ```tsx
 * const { environments, getEnvironment, maxFeaturesAllowed, isLoading } =
 *   useProjectEnvironments(projectId)
 *
 * const env = getEnvironment(apiKey)
 * const canAddFeature = maxFeaturesAllowed === null || features.length < maxFeaturesAllowed
 * ```
 */
export function useProjectEnvironments(projectId: number): {
  project: Project | undefined
  environments: Environment[]
  getEnvironmentIdFromKey: (apiKey: string) => number | undefined
  getEnvironment: (apiKey: string) => Environment | undefined
  maxFeaturesAllowed: number | null
  isLoading: boolean
  error: unknown
} {
  const {
    data: project,
    error: projectError,
    isLoading: isLoadingProject,
  } = useGetProjectQuery({ id: projectId }, { skip: !projectId })

  const {
    data: environmentsData,
    error: environmentsError,
    isLoading: isLoadingEnvironments,
  } = useGetEnvironmentsQuery({ projectId }, { skip: !projectId })

  const environments = useMemo(
    () => environmentsData?.results ?? [],
    [environmentsData?.results],
  )

  const getEnvironmentIdFromKey = useCallback(
    (apiKey: string): number | undefined => {
      return environments.find((env) => env.api_key === apiKey)?.id
    },
    [environments],
  )

  const getEnvironment = useCallback(
    (apiKey: string): Environment | undefined => {
      return environments.find((env) => env.api_key === apiKey)
    },
    [environments],
  )

  return {
    environments,
    error: projectError || environmentsError,
    getEnvironment,
    getEnvironmentIdFromKey,
    isLoading: isLoadingProject || isLoadingEnvironments,
    maxFeaturesAllowed: project?.max_features_allowed ?? null,
    project,
  }
}
