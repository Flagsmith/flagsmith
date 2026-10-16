import { useMemo } from 'react'
import { ProjectFlag } from 'common/types/responses'
import {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
  useGetFeatureDependenciesQuery,
  useGetFeatureDependentsQuery,
} from 'common/services/useFeatureDependency'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
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
  // in this environment comes from the feature list.
  const featureStates = useFeatureStates({ environmentId, projectId })

  const rows = useMemo(
    () =>
      toPrerequisiteRows(dependencies?.results ?? [], featureStates.features),
    [dependencies, featureStates.features],
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
    isError: isDependenciesError || isDependentsError || featureStates.isError,
    isLoading:
      isLoadingDependencies || isLoadingDependents || featureStates.isLoading,
    remove: (prerequisiteFeatureId: number) =>
      deleteDependency({
        environmentId,
        featureId,
        prerequisiteFeatureId,
      }).unwrap(),
    rows,
  }
}
