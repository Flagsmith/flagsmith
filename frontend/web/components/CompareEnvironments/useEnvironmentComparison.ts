import { useCallback, useEffect, useRef, useState } from 'react'
import sortBy from 'lodash/sortBy'
import data from 'common/data/base/_data'
import Project from 'common/project'
import ProjectStore from 'common/stores/project-store'
import { hasMultivariateChange } from 'common/utils/compareMultivariate'
import { Environment, FeatureState, ProjectFlag } from 'common/types/responses'
import { FeatureChange } from './types'

type UseEnvironmentComparisonArgs = {
  projectId: string
  leftEnvironmentKey: string
  rightEnvironmentKey: string
}

const deriveChanges = (
  leftProjectFlags: ProjectFlag[],
  rightProjectFlags: ProjectFlag[],
  leftFlags: FeatureState[],
  rightFlags: FeatureState[],
): FeatureChange[] => {
  const changes: FeatureChange[] = []

  sortBy(leftProjectFlags, (p) => p.name).forEach((projectFlagLeft) => {
    const projectFlagRight = rightProjectFlags.find(
      (pf) => pf.id === projectFlagLeft.id,
    )
    const leftSide = leftFlags.find((v) => v.feature === projectFlagLeft.id)
    const rightSide = rightFlags.find((v) => v.feature === projectFlagLeft.id)

    if (!leftSide || !rightSide) return

    const enabledChanged = rightSide.enabled !== leftSide.enabled
    const valueChanged =
      rightSide.feature_state_value !== leftSide.feature_state_value
    const multivariateChanged = hasMultivariateChange(leftSide, rightSide)

    const hasDiff =
      enabledChanged ||
      valueChanged ||
      multivariateChanged ||
      !!projectFlagLeft.num_segment_overrides ||
      !!projectFlagRight?.num_segment_overrides

    changes.push({
      enabledChanged,
      hasDiff,
      leftEnabled: leftSide.enabled,
      leftEnvironmentFlag: leftSide,
      leftValue: leftSide.feature_state_value,
      multivariateChanged,
      projectFlagLeft,
      projectFlagRight,
      rightEnabled: rightSide.enabled,
      rightEnvironmentFlag: rightSide,
      rightValue: rightSide.feature_state_value,
      valueChanged,
    })
  })

  return changes
}

export const useEnvironmentComparison = ({
  leftEnvironmentKey,
  projectId,
  rightEnvironmentKey,
}: UseEnvironmentComparisonArgs) => {
  const [changes, setChanges] = useState<FeatureChange[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(false)

  // Bumped on every run so a slow earlier response can't overwrite the
  // result of a newer comparison (overlapping-fetch guard)
  const requestId = useRef(0)

  const refresh = useCallback(async () => {
    if (!leftEnvironmentKey || !rightEnvironmentKey) {
      return
    }

    const currentRequest = ++requestId.current
    setIsLoading(true)
    setError(false)

    const leftEnvironmentId =
      ProjectStore.getEnvironmentIdFromKey(leftEnvironmentKey)
    const rightEnvironmentId =
      ProjectStore.getEnvironmentIdFromKey(rightEnvironmentKey)

    try {
      const [leftProjectFlags, rightProjectFlags, leftFlags, rightFlags] =
        await Promise.all([
          data.get(
            `${Project.api}projects/${projectId}/features/?page_size=999&environment=${leftEnvironmentId}`,
          ),
          data.get(
            `${Project.api}projects/${projectId}/features/?page_size=999&environment=${rightEnvironmentId}`,
          ),
          data.get(
            `${Project.api}environments/${leftEnvironmentKey}/featurestates/?page_size=999`,
          ),
          data.get(
            `${Project.api}environments/${rightEnvironmentKey}/featurestates/?page_size=999`,
          ),
        ])

      if (currentRequest !== requestId.current) return

      setChanges(
        deriveChanges(
          leftProjectFlags.results || [],
          rightProjectFlags.results || [],
          leftFlags.results || [],
          rightFlags.results || [],
        ),
      )
    } catch {
      if (currentRequest !== requestId.current) return
      setError(true)
    } finally {
      if (currentRequest === requestId.current) {
        setIsLoading(false)
      }
    }
  }, [leftEnvironmentKey, rightEnvironmentKey, projectId])

  useEffect(() => {
    refresh()
  }, [refresh])

  const leftEnvironment = ProjectStore.getEnvironment(leftEnvironmentKey) as
    | Environment
    | undefined
    | null
  const rightEnvironment = ProjectStore.getEnvironment(rightEnvironmentKey) as
    | Environment
    | undefined
    | null

  return {
    changes,
    error,
    isLoading,
    leftEnvironment,
    leftEnvironmentId: ProjectStore.getEnvironmentIdFromKey(leftEnvironmentKey),
    refresh,
    rightEnvironment,
    rightEnvironmentId:
      ProjectStore.getEnvironmentIdFromKey(rightEnvironmentKey),
  }
}
