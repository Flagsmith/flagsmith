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
  const decision = shouldDeepFetchFeature({
    featureParam,
    isListLoaded,
    projectFlags,
  })

  const environmentNumericId = environmentApiKey
    ? getEnvironmentIdFromKey(environmentApiKey)
    : undefined

  const { data: projectFlag, isError } = useGetProjectFlagQuery(
    decision ? { id: decision.featureId, project: projectId } : skipToken,
  )

  const { data: featureStatesData } = useGetFeatureStatesQuery(
    decision && environmentNumericId
      ? { environment: environmentNumericId, feature: decision.featureId }
      : skipToken,
  )

  return useMemo(() => {
    if (!decision || isError || !projectFlag) {
      return null
    }
    return {
      environmentFlag: pickEnvironmentFlag(
        featureStatesData?.results,
        decision.featureId,
      ),
      projectFlag,
    }
  }, [decision, isError, projectFlag, featureStatesData])
}
