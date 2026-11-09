import { useMemo } from 'react'
import { ProjectFlag } from 'common/types/responses'
import {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
  useGetFeatureDependenciesQuery,
  useGetFeatureDependentsQuery,
} from 'common/services/useFeatureDependency'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
import {
  hasPrerequisiteStates,
  toPrerequisiteRows,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/prerequisiteState'

type UseDependenciesArgs = {
  environmentId: string
  featureId: number
  projectId: number
  skip?: boolean
}

export const useDependencies = ({
  environmentId,
  featureId,
  projectId,
  skip = false,
}: UseDependenciesArgs) => {
  const query = { environmentId, featureId }
  const {
    data: dependencies,
    isError: isDependenciesError,
    isLoading: isLoadingDependencies,
  } = useGetFeatureDependenciesQuery(query, { skip })
  const { data: dependents } = useGetFeatureDependentsQuery(query, { skip })

  const [createDependency, { isLoading: isCreating }] =
    useCreateFeatureDependencyMutation()
  const [deleteDependency] = useDeleteFeatureDependencyMutation()

  // The edges carry only the prerequisite's name and id, so its current state
  // in this environment comes from the feature list.
  const featureStates = useFeatureStates({ environmentId, projectId, skip })
  const prerequisites = dependencies?.results ?? []
  const hasAllPrerequisiteStates = hasPrerequisiteStates(
    prerequisites,
    featureStates.features,
  )
  const isReady =
    !skip &&
    !isDependenciesError &&
    !isLoadingDependencies &&
    !featureStates.isLoading &&
    !featureStates.isError &&
    featureStates.hasLoadedFeatures &&
    hasAllPrerequisiteStates

  const rows = useMemo(
    () =>
      isReady
        ? toPrerequisiteRows(
            dependencies?.results ?? [],
            featureStates.features,
          )
        : [],
    [dependencies, featureStates.features, isReady],
  )

  const isLoading =
    !skip &&
    (isLoadingDependencies ||
      featureStates.isLoading ||
      (!featureStates.isError && !featureStates.hasLoadedFeatures) ||
      (!isDependenciesError &&
        !isLoadingDependencies &&
        !hasAllPrerequisiteStates))

  return {
    add: (prerequisite: ProjectFlag) =>
      createDependency({
        environmentId,
        featureId,
        prerequisiteFeatureId: prerequisite.id,
      }).unwrap(),
    dependentEdges: dependents?.results ?? [],
    isCreating,
    isEnabled: featureStates.isEnabled,
    // Prerequisite status does not rely on dependents loading successfully.
    isError: isDependenciesError || featureStates.isError,
    isLoading,
    isReady,
    remove: (prerequisiteFeatureId: number) =>
      deleteDependency({
        environmentId,
        featureId,
        prerequisiteFeatureId,
      }).unwrap(),
    rows,
  }
}
