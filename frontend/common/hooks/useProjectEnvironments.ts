import { useCallback, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetProjectQuery } from 'common/services/useProject'
import type { Environment, Project } from 'common/types/responses'

/**
 * Custom hook for fetching and managing project and environment data.
 *
 * Provides raw project and environment data along with convenient accessor functions
 * for looking up environments by API key. This is a general-purpose hook that can be
 * used across the application whenever both project and environment data are needed.
 *
 * @param projectId - The project ID to fetch data for
 * @returns Object containing project data, environments, accessor functions, and loading/error states
 *
 * @example
 * ```tsx
 * const { project, environments, getEnvironment, isLoading } = useProjectEnvironments(projectId)
 *
 * // Access project properties
 * const maxFeatures = project?.max_features_allowed
 *
 * // Look up environment by API key
 * const env = getEnvironment(apiKey)
 * const requiresApprovals = env?.minimum_change_request_approvals
 *
 * // Access all environments
 * const envCount = environments.length
 * ```
 */
export function useProjectEnvironments(projectId: number): {
  project: Project | undefined
  environments: Environment[]
  getEnvironmentIdFromKey: (apiKey: string) => number | undefined
  getEnvironment: (apiKey: string) => Environment | undefined
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
    project,
  }
}
