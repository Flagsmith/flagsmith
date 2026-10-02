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
import { toPrerequisiteRows } from './prerequisiteState'

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
  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)
  const { data: featureList } = useGetFeatureListQuery(
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
    isError: isDependenciesError || isDependentsError,
    isLoading: isLoadingDependencies || isLoadingDependents,
    remove: (prerequisiteFeatureId: number) =>
      deleteDependency({
        environmentId,
        featureId,
        prerequisiteFeatureId,
      }).unwrap(),
    rows,
  }
}
