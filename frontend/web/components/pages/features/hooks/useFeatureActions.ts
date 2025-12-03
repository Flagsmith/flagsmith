import { useCallback } from 'react'
import { useRemoveProjectFlagMutation } from 'common/services/useProjectFlag'
import { useUpdateFeatureStateMutation } from 'common/services/useFeatureList'
import type { FeatureState, ProjectFlag } from 'common/types/responses'

/**
 * Custom hook for feature flag actions (toggle, remove).
 *
 * Uses closure pattern to capture projectId/environmentId at hook creation.
 * The returned callbacks match FeatureRow's expected signature for compatibility.
 *
 * @param projectId - The project ID for feature operations
 * @param environmentId - The environment ID for toggle operations
 * @returns Object with removeFlag and toggleFlag callbacks
 *
 * @example
 * ```tsx
 * const { removeFlag, toggleFlag } = useFeatureActions(projectId, environmentId)
 *
 * // Remove a feature
 * await removeFlag(projectId, projectFlag)
 *
 * // Toggle a feature
 * await toggleFlag(projectId, environmentId, flag, environmentFlag)
 * ```
 *
 * TODO: Clean up after migrating all FeatureRow consumers to modern patterns:
 * - CompareFeatures.js (uses FeatureListProvider - legacy Flux)
 * - CompareEnvironments.js (uses FeatureListProvider - legacy Flux)
 * - WidgetPage.tsx (uses FeatureListProvider - legacy Flux)
 *
 * Once migrated, FeatureRow's callback signatures can be simplified.
 */
export function useFeatureActions(
  projectId: number,
  environmentId: string,
): {
  removeFlag: (projectId: number, projectFlag: ProjectFlag) => Promise<void>
  toggleFlag: (
    projectId: number,
    environmentId: string,
    flag: ProjectFlag,
    environmentFlag: FeatureState | undefined,
  ) => Promise<void>
} {
  const [removeProjectFlag] = useRemoveProjectFlagMutation()
  const [updateFeatureState] = useUpdateFeatureStateMutation()

  const removeFlag = useCallback(
    async (_projectId: number, projectFlag: ProjectFlag) => {
      try {
        await removeProjectFlag({
          id: projectFlag.id,
          project: projectId,
        }).unwrap()
        toast(`Removed feature: ${projectFlag.name}`)
      } catch (error) {
        console.error('Failed to remove feature:', error)
        toast('Failed to remove feature', 'danger')
      }
    },
    [projectId, removeProjectFlag],
  )

  const toggleFlag = useCallback(
    async (
      _projectId: number,
      _environmentId: string,
      flag: ProjectFlag,
      environmentFlag: FeatureState | undefined,
    ) => {
      if (!environmentFlag) return

      try {
        await updateFeatureState({
          body: {
            enabled: !environmentFlag.enabled,
          },
          environmentFlagId: environmentFlag.id,
          environmentId,
        }).unwrap()
      } catch (error) {
        console.error('Failed to toggle feature:', error)
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
