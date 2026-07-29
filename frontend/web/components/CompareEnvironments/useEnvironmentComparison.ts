import { useCallback, useMemo } from 'react'
import sortBy from 'lodash/sortBy'
import ProjectStore from 'common/stores/project-store'
import { hasMultivariateChange } from 'common/utils/compareMultivariate'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useGetAllEnvironmentFeatureStatesQuery } from 'common/services/useFeatureState'
import { Environment, FeatureState, ProjectFlag } from 'common/types/responses'
import { FeatureChange } from './types'

type UseEnvironmentComparisonArgs = {
  projectId: string
  leftEnvironmentKey: string
  rightEnvironmentKey: string
}

// ProjectStore.getEnvironment returns null while the project is loading and
// undefined for unknown keys
type StoredEnvironment = Environment | undefined | null

const deriveChanges = (
  leftProjectFlags: ProjectFlag[],
  rightProjectFlags: ProjectFlag[],
  leftFlags: FeatureState[],
  rightFlags: FeatureState[],
): FeatureChange[] => {
  const changes: FeatureChange[] = []

  // Pre-index for O(1) lookups instead of O(n) .find() calls
  const rightProjectFlagsById = new Map(
    rightProjectFlags.map((pf) => [pf.id, pf]),
  )
  const leftFlagsByFeatureId = new Map(leftFlags.map((fs) => [fs.feature, fs]))
  const rightFlagsByFeatureId = new Map(
    rightFlags.map((fs) => [fs.feature, fs]),
  )

  sortBy(leftProjectFlags, (p) => p.name).forEach((projectFlagLeft) => {
    const projectFlagRight = rightProjectFlagsById.get(projectFlagLeft.id)
    const leftSide = leftFlagsByFeatureId.get(projectFlagLeft.id)
    const rightSide = rightFlagsByFeatureId.get(projectFlagLeft.id)

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
  const leftEnvironmentId =
    ProjectStore.getEnvironmentIdFromKey(leftEnvironmentKey)
  const rightEnvironmentId =
    ProjectStore.getEnvironmentIdFromKey(rightEnvironmentKey)

  const {
    currentData: leftProjectFlags,
    isError: leftProjectFlagsError,
    isFetching: leftProjectFlagsFetching,
    refetch: refetchLeftProjectFlags,
  } = useGetProjectFlagsQuery(
    { environment: leftEnvironmentId, project: projectId },
    { skip: !leftEnvironmentId },
  )

  const {
    currentData: rightProjectFlags,
    isError: rightProjectFlagsError,
    isFetching: rightProjectFlagsFetching,
    refetch: refetchRightProjectFlags,
  } = useGetProjectFlagsQuery(
    { environment: rightEnvironmentId, project: projectId },
    { skip: !rightEnvironmentId },
  )

  const {
    currentData: leftFlags,
    isError: leftFlagsError,
    isFetching: leftFlagsFetching,
    refetch: refetchLeftFlags,
  } = useGetAllEnvironmentFeatureStatesQuery(
    { environmentKey: leftEnvironmentKey },
    { skip: !leftEnvironmentKey },
  )

  const {
    currentData: rightFlags,
    isError: rightFlagsError,
    isFetching: rightFlagsFetching,
    refetch: refetchRightFlags,
  } = useGetAllEnvironmentFeatureStatesQuery(
    { environmentKey: rightEnvironmentKey },
    { skip: !rightEnvironmentKey },
  )

  const changes = useMemo(() => {
    if (!leftProjectFlags || !rightProjectFlags || !leftFlags || !rightFlags) {
      return null
    }
    return deriveChanges(
      leftProjectFlags.results || [],
      rightProjectFlags.results || [],
      leftFlags.results || [],
      rightFlags.results || [],
    )
  }, [leftProjectFlags, rightProjectFlags, leftFlags, rightFlags])

  const refresh = useCallback(() => {
    refetchLeftProjectFlags()
    refetchRightProjectFlags()
    refetchLeftFlags()
    refetchRightFlags()
  }, [
    refetchLeftProjectFlags,
    refetchRightProjectFlags,
    refetchLeftFlags,
    refetchRightFlags,
  ])

  const leftEnvironment = ProjectStore.getEnvironment(
    leftEnvironmentKey,
  ) as StoredEnvironment
  const rightEnvironment = ProjectStore.getEnvironment(
    rightEnvironmentKey,
  ) as StoredEnvironment

  return {
    changes,
    error:
      leftProjectFlagsError ||
      rightProjectFlagsError ||
      leftFlagsError ||
      rightFlagsError,
    isLoading:
      leftProjectFlagsFetching ||
      rightProjectFlagsFetching ||
      leftFlagsFetching ||
      rightFlagsFetching,
    leftEnvironment,
    leftEnvironmentId,
    refresh,
    rightEnvironment,
    rightEnvironmentId,
  }
}
