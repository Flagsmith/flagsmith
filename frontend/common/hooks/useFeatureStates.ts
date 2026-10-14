import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from './useProjectEnvironments'
import { ProjectFlag } from 'common/types/responses'

// Stable, so a memo over the list doesn't rerun while it loads.
const NO_FEATURES: ProjectFlag[] = []

// Whether each of a project's features is on in one environment, from the
// feature list. getFeatureList takes the numeric environment id, not the key.
export const useFeatureStates = (projectId: number, environmentKey: string) => {
  const {
    error: environmentsError,
    getEnvironmentIdFromKey,
    isLoading: isLoadingEnvironments,
  } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentKey)
  const {
    data,
    isError: isFeatureListError,
    isLoading: isLoadingFeatureList,
  } = useGetFeatureListQuery(
    {
      environmentId: String(numericEnvId ?? ''),
      page: 1,
      // One page has to cover every feature, or one outside it reads as off.
      page_size: 999,
      projectId,
    },
    { skip: !numericEnvId },
  )

  const features = data?.results ?? NO_FEATURES
  return {
    features,
    isError:
      isFeatureListError ||
      !!environmentsError ||
      // The lookup finished without finding the environment, so the feature
      // list will never run and nothing is coming.
      (!isLoadingEnvironments && !numericEnvId),
    isLoading: isLoadingEnvironments || isLoadingFeatureList,
  }
}
