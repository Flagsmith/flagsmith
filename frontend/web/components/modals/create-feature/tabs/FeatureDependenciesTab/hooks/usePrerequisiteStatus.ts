import { useMemo } from 'react'
import { useGetFeatureDependenciesQuery } from 'common/services/useFeatureDependency'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
import {
  PrerequisiteRow,
  toPrerequisiteRows,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/prerequisiteState'

type UsePrerequisiteStatusArgs = {
  environmentId: string
  featureId: number
  projectId: number
  skip?: boolean
}

/**
 * Whether each of a flag's prerequisites is on, for showing outside the
 * Dependencies tab. Shares its requests with useDependencies.
 *
 * Undefined until both the dependencies and the feature list are in, as every
 * prerequisite reads as off without the latter.
 */
export const usePrerequisiteStatus = ({
  environmentId,
  featureId,
  projectId,
  skip,
}: UsePrerequisiteStatusArgs): PrerequisiteRow[] | undefined => {
  // currentData, not data, which keeps another flag's or environment's
  // dependencies while these load.
  const {
    currentData: dependencies,
    isError,
    isLoading,
  } = useGetFeatureDependenciesQuery({ environmentId, featureId }, { skip })
  const featureStates = useFeatureStates({ environmentId, projectId, skip })
  const rows = useMemo(
    () =>
      toPrerequisiteRows(dependencies?.results ?? [], featureStates.features),
    [dependencies, featureStates.features],
  )
  const isReady =
    !skip &&
    !!dependencies &&
    !isLoading &&
    !isError &&
    !featureStates.isLoading &&
    !featureStates.isError
  return isReady ? rows : undefined
}
