import { useMemo } from 'react'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { getFeatureStateCrud } from 'common/services/useFeatureVersion'
import { ChangeSet, FeatureState } from 'common/types/responses'

interface UseFeatureStateChangesParams {
  projectId: string | number
  environmentId: number
  featureId?: number
  featureStates?: FeatureState[]
  changeSets?: ChangeSet[]
}

export const useHasFeatureStateChanges = ({
  changeSets,
  environmentId,
  featureId,
  featureStates,
  projectId,
}: UseFeatureStateChangesParams): boolean => {
  const shouldUseChangeSets = changeSets !== undefined && changeSets.length > 0

  const { data: featureStatesData } = useGetFeatureStatesQuery(
    {
      environment: Number(environmentId),
      feature: featureId,
    },
    {
      skip: shouldUseChangeSets || !environmentId || !featureId,
    },
  )

  const { data: segmentsData } = useGetSegmentsQuery(
    {
      include_feature_specific: true,
      page_size: 1000,
      projectId: String(projectId),
    },
    {
      skip: shouldUseChangeSets || !projectId,
    },
  )

  const changes = useMemo(() => {
    if (shouldUseChangeSets) {
      return changeSets.some(
        (changeSet: ChangeSet) =>
          changeSet.feature_states_to_create.length > 0 ||
          changeSet.feature_states_to_update.length > 0 ||
          changeSet.segment_ids_to_delete_overrides.length > 0,
      )
    }
    if (!featureStatesData?.results || !featureStates) {
      return true
    }

    const oldFeatureStates = featureStatesData.results
    const segments = segmentsData?.results

    const {
      feature_states_to_create,
      feature_states_to_update,
      segment_ids_to_delete_overrides,
    } = getFeatureStateCrud(featureStates, oldFeatureStates, segments)

    const hasChanges =
      feature_states_to_create.length > 0 ||
      feature_states_to_update.length > 0 ||
      segment_ids_to_delete_overrides.length > 0

    return hasChanges
  }, [
    featureStatesData,
    changeSets,
    shouldUseChangeSets,
    featureStates,
    segmentsData,
  ])

  return changes
}
