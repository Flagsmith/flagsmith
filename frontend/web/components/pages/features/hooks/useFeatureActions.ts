import { useCallback } from 'react'
import { useRemoveProjectFlagMutation } from 'common/services/useProjectFlag'
import { useUpdateFeatureStateMutation } from 'common/services/useFeatureList'
import type { ProjectFlag } from 'common/types/responses'
import type { EnvironmentFlagsMap } from 'components/pages/features/types'

/**
 * Custom hook for feature actions (remove, toggle) with toast notifications
 * Follows the pattern from settings pages (useUpdateWithToast)
 *
 * Note: Metrics refresh automatically via RTK Query cache invalidation.
 * The mutations invalidate the METRICS tag, triggering automatic refetch.
 */
export function useFeatureActions(projectId: string, environmentId: string) {
  const [removeProjectFlag] = useRemoveProjectFlagMutation()
  const [updateFeatureState] = useUpdateFeatureStateMutation()

  const removeFlag = useCallback(
    async (projectFlag: ProjectFlag) => {
      try {
        await removeProjectFlag({
          id: projectFlag.id,
          project: projectId,
        }).unwrap()
        toast(`Removed feature: ${projectFlag.name}`)
      } catch (error) {
        toast('Failed to remove feature', 'danger')
      }
    },
    [projectId, removeProjectFlag],
  )

  const toggleFlag = useCallback(
    async (flag: ProjectFlag, environmentFlags: EnvironmentFlagsMap) => {
      const environmentFlag = environmentFlags[flag.id]
      if (!environmentFlag) return

      try {
        await updateFeatureState({
          body: {
            enabled: !environmentFlag.enabled,
          },
          environmentId,
          stateId: environmentFlag.id,
        }).unwrap()
      } catch (error) {
        toast('Failed to toggle feature', 'danger')
      }
    },
    [environmentId, updateFeatureState],
  )

  return {
    removeFlag,
    toggleFlag,
  }
}
