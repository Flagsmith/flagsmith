import { useState, useCallback } from 'react'
import { useRemoveProjectFlagMutation } from 'common/services/useProjectFlag'
import { useUpdateFeatureStateMutation } from 'common/services/useFeatureList'

/**
 * Custom hook for feature actions (remove, toggle) with toast notifications
 * Follows the pattern from settings pages (useUpdateWithToast)
 */
export function useFeatureActions(projectId: string, environmentId: string) {
  const [forceMetricsRefetch, setForceMetricsRefetch] = useState(false)

  const [removeProjectFlag] = useRemoveProjectFlagMutation()
  const [updateFeatureState] = useUpdateFeatureStateMutation()

  const toggleForceMetricsRefetch = useCallback(() => {
    setForceMetricsRefetch((prev) => !prev)
  }, [])

  const removeFlag = useCallback(
    async (projectFlag: any) => {
      try {
        await removeProjectFlag({
          id: projectFlag.id,
          project: projectId,
        }).unwrap()
        toggleForceMetricsRefetch()
        toast(`Removed feature: ${projectFlag.name}`)
      } catch (error) {
        toast('Failed to remove feature', 'danger')
      }
    },
    [projectId, removeProjectFlag, toggleForceMetricsRefetch],
  )

  const toggleFlag = useCallback(
    async (flag: any, environmentFlags: any) => {
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
        toggleForceMetricsRefetch()
      } catch (error) {
        toast('Failed to toggle feature', 'danger')
      }
    },
    [environmentId, updateFeatureState, toggleForceMetricsRefetch],
  )

  return {
    forceMetricsRefetch,
    removeFlag,
    toggleFlag,
    toggleForceMetricsRefetch,
  }
}
