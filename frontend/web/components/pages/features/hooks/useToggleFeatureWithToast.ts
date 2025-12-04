import { useCallback } from 'react'
import { useUpdateFeatureStateMutation } from 'common/services/useFeatureList'
import type { FeatureState, ProjectFlag } from 'common/types/responses'

type ToggleFeatureOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
  onSuccess?: () => void
}

/**
 * Hook for toggling a feature flag's enabled state with toast notifications.
 *
 * Follows the standard "withToast" pattern used across the application.
 * Returns mutation state for loading/error indicators.
 *
 * @returns Tuple of [toggleWithToast function, mutation state]
 *
 * @example
 * ```tsx
 * const [toggleFeature, { isLoading }] = useToggleFeatureWithToast()
 *
 * await toggleFeature(flag, environmentFlag, environmentId, {
 *   successMessage: 'Feature toggled',
 *   onSuccess: () => console.log('Done!'),
 * })
 * ```
 */
export const useToggleFeatureWithToast = () => {
  const [updateFeatureState, state] = useUpdateFeatureStateMutation()

  const toggleWithToast = useCallback(
    async (
      flag: ProjectFlag,
      environmentFlag: FeatureState | undefined,
      environmentId: string,
      options?: ToggleFeatureOptions,
    ) => {
      if (!environmentFlag) {
        console.warn('Cannot toggle feature: environmentFlag is undefined')
        return
      }

      try {
        await updateFeatureState({
          body: {
            enabled: !environmentFlag.enabled,
          },
          environmentFlagId: environmentFlag.id,
          environmentId,
        }).unwrap()

        if (options?.successMessage) {
          toast(options.successMessage)
        }
        options?.onSuccess?.()
      } catch (error) {
        console.error('Failed to toggle feature:', error)
        toast(
          options?.errorMessage ||
            'Failed to toggle feature. Please try again.',
          'danger',
        )
        options?.onError?.(error)
      }
    },
    [updateFeatureState],
  )

  return [toggleWithToast, state] as const
}
