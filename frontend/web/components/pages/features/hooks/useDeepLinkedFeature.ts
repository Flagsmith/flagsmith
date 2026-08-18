import { useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import Utils from 'common/utils/utils'
import type { FeatureState, ProjectFlag } from 'common/types/responses'
import {
  pickEnvironmentFlag,
  shouldDeepFetchFeature,
} from './deepLinkedFeature'

type DeepLinkedFeature = {
  projectFlag: ProjectFlag
  environmentFlag: FeatureState | undefined
}

/**
 * Supports deep-linking to a feature slideout (`?feature=<id>`) when the targeted
 * feature is not on the current page of the paginated list. The page renders a
 * hidden FeatureRow for the returned feature so its existing deep-link effect can
 * open the slideout. Returns `null` when no direct fetch is needed or possible.
 */
export function useDeepLinkedFeature(args: {
  projectId: number
  environmentApiKey: string
  getEnvironmentIdFromKey: (apiKey: string) => number | undefined
  projectFlags: ProjectFlag[]
  isListLoaded: boolean
}): DeepLinkedFeature | null {
  const {
    environmentApiKey,
    getEnvironmentIdFromKey,
    isListLoaded,
    projectFlags,
    projectId,
  } = args

  const featureParam = (Utils.fromParam() as Record<string, string>).feature
  const decision = useMemo(
    () => shouldDeepFetchFeature({ featureParam, isListLoaded, projectFlags }),
    [featureParam, isListLoaded, projectFlags],
  )

  const environmentNumericId = environmentApiKey
    ? getEnvironmentIdFromKey(environmentApiKey)
    : undefined

  const { data: projectFlag, isError } = useGetProjectFlagQuery(
    decision ? { id: decision.featureId, project: projectId } : skipToken,
  )

  const { data: featureStatesData, isFetching: isFetchingFeatureStates } =
    useGetFeatureStatesQuery(
      decision && environmentNumericId
        ? { environment: environmentNumericId, feature: decision.featureId }
        : skipToken,
    )

  // When the feature has an environment, hold off until its state has resolved
  // so the slideout opens with the real enabled/value state rather than blanks.
  // The two queries fire together but settle independently, and the slideout is
  // opened with a one-time snapshot, so a late feature state would never reach
  // it. When no environment id is known we can't fetch state, so open anyway.
  const awaitingFeatureState =
    !!decision &&
    !!environmentNumericId &&
    (isFetchingFeatureStates || !featureStatesData)

  return useMemo(() => {
    if (!decision || isError || !projectFlag || awaitingFeatureState) {
      return null
    }
    return {
      environmentFlag: pickEnvironmentFlag(
        featureStatesData?.results,
        decision.featureId,
      ),
      projectFlag,
    }
  }, [decision, isError, projectFlag, featureStatesData, awaitingFeatureState])
}
