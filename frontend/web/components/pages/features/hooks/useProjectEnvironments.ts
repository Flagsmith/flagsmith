import { useCallback, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetProjectQuery } from 'common/services/useProject'
import type { Environment } from 'common/types/responses'

export function useProjectEnvironments(projectId: string) {
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
    () => environmentsData?.results || [],
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
