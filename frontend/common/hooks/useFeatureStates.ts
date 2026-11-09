import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { ProjectFlag } from 'common/types/responses'
import { useProjectEnvironments } from './useProjectEnvironments'

// Stable, so consumers do not see a new empty list while loading.
const NO_FEATURES: ProjectFlag[] = []
type UseFeatureStatesArgs = {
  // The api key, as everywhere else in the UI.
  environmentId: string
  projectId: number
  skip?: boolean
}

// Whether each feature is on in one environment, from all project flags.
// The recursive project-flags query follows every page.
export const useFeatureStates = ({
  environmentId,
  projectId,
  skip,
}: UseFeatureStatesArgs) => {
  const {
    error: environmentsError,
    getEnvironmentIdFromKey,
    isLoading: isLoadingEnvironments,
  } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)
  const {
    currentData: data,
    isError: isFeatureListError,
    isFetching: isLoadingFeatureList,
  } = useGetProjectFlagsQuery(
    {
      environment: numericEnvId,
      project: String(projectId),
    },
    { skip: skip || !numericEnvId },
  )

  const features = data?.results ?? NO_FEATURES
  return {
    features,
    hasLoadedFeatures: data !== undefined,
    isEnabled: (featureId: number) =>
      !!features.find((feature) => feature.id === featureId)
        ?.environment_feature_state?.enabled,
    isError:
      isFeatureListError ||
      !!environmentsError ||
      // The lookup finished without finding the environment, so the feature
      // list will never run and nothing is coming.
      (!isLoadingEnvironments && !numericEnvId),
    isLoading: isLoadingEnvironments || isLoadingFeatureList,
  }
}
