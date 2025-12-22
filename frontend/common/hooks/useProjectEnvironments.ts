import { useCallback, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetProjectQuery } from 'common/services/useProject'
import type { Environment, Project } from 'common/types/responses'

interface UseProjectEnvironmentsResult {
  project: Project | undefined
  environments: Environment[]
  getEnvironmentIdFromKey: (apiKey: string) => number | undefined
  getEnvironment: (apiKey: string) => Environment | undefined
  isLoading: boolean
  error: Error | undefined
}

/** Fetches project and environment data with accessor functions for API key lookups. */
export function useProjectEnvironments(
  projectId: number,
): UseProjectEnvironmentsResult {
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
