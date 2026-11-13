import { useCallback } from 'react'
import { useToggleFeatureMutation } from 'common/services/useFeatureState'
import type {
  Environment,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'

type ToggleFeatureOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
  onSuccess?: () => void
}

/** Toggles a feature flag's enabled state with toast notifications. */
export const useToggleFeatureWithToast = () => {
  const [toggleFeature, { isLoading }] = useToggleFeatureMutation()

  const toggleWithToast = useCallback(
    async (
      flag: ProjectFlag,
      environmentFlag: FeatureState | undefined,
      environment: Environment,
      options?: ToggleFeatureOptions,
    ) => {
      if (!environmentFlag) {
        console.warn('Cannot toggle feature: environmentFlag is undefined')
        options?.onError?.(new Error('environmentFlag is undefined'))
        return
      }
      try {
        await toggleFeature({
          environment,
          environmentFlag,
          projectFlag: flag,
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
    [toggleFeature],
  )

  return [toggleWithToast, { isLoading }] as const
}
