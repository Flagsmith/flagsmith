import { useMemo } from 'react'
import { ProjectFlag } from 'common/types/responses'
import {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
  useGetFeatureDependenciesQuery,
  useGetFeatureDependentsQuery,
} from 'common/services/useFeatureDependency'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { toPrerequisiteRows } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/prerequisiteState'

type UseDependenciesArgs = {
  environmentId: string
  featureId: number
  projectId: number
}

export const useDependencies = ({
  environmentId,
  featureId,
  projectId,
}: UseDependenciesArgs) => {
  const query = { environmentId, featureId }
  const {
    data: dependencies,
    isError: isDependenciesError,
    isLoading: isLoadingDependencies,
  } = useGetFeatureDependenciesQuery(query)
  const {
    data: dependents,
    isError: isDependentsError,
    isLoading: isLoadingDependents,
  } = useGetFeatureDependentsQuery(query)

  const [createDependency, { isLoading: isCreating }] =
    useCreateFeatureDependencyMutation()
  const [deleteDependency] = useDeleteFeatureDependencyMutation()

  // The edges carry only the prerequisite's name and id, so its current state
  // in this environment comes from the feature list. getFeatureList parses
  // environmentId as the numeric id, not the api key.
  const {
    error: environmentsError,
    getEnvironmentIdFromKey,
    isLoading: isLoadingEnvironments,
  } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)
  const {
    data: featureList,
    isError: isFeatureListError,
    isLoading: isLoadingFeatureList,
  } = useGetFeatureListQuery(
    {
      environmentId: String(numericEnvId ?? ''),
      page: 1,
      // One page has to cover every prerequisite, or one outside it reads as
      // unmet and the banner claims the flag is serving off.
      page_size: 999,
      projectId,
    },
    { skip: !numericEnvId },
  )

  const rows = useMemo(
    () =>
      toPrerequisiteRows(
        dependencies?.results ?? [],
        featureList?.results ?? [],
      ),
    [dependencies, featureList],
  )

  return {
    add: (prerequisite: ProjectFlag) =>
      createDependency({
        environmentId,
        featureId,
        prerequisiteFeatureId: prerequisite.id,
      }).unwrap(),
    dependentEdges: dependents?.results ?? [],
    isCreating,
    // The feature list counts too. Without it every prerequisite reads as off,
    // so the tab would claim the flag is serving off while the list is still
    // in flight, or for good if the request fails.
    isError:
      isDependenciesError ||
      isDependentsError ||
      isFeatureListError ||
      !!environmentsError ||
      // The lookup finished without finding the environment, so the feature
      // list will never run and nothing is coming.
      (!isLoadingEnvironments && !numericEnvId),
    isLoading:
      isLoadingDependencies ||
      isLoadingDependents ||
      isLoadingEnvironments ||
      isLoadingFeatureList,
    remove: (prerequisiteFeatureId: number) =>
      deleteDependency({
        environmentId,
        featureId,
        prerequisiteFeatureId,
      }).unwrap(),
    rows,
  }
}
