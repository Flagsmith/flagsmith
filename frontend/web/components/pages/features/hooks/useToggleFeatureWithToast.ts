import { useCallback } from 'react'
import { useUpdateFeatureStateMutation } from 'common/services/useFeatureState'
import { useCreateAndSetFeatureVersionMutation } from 'common/services/useFeatureVersion'
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
  const [updateFeatureState, updateState] = useUpdateFeatureStateMutation()
  const [createAndSetFeatureVersion, versionState] =
    useCreateAndSetFeatureVersionMutation()

  const toggleWithToast = useCallback(
    async (
      flag: ProjectFlag,
      environmentFlag: FeatureState | undefined,
      environment: Environment,
      options?: ToggleFeatureOptions,
    ) => {
      if (!environmentFlag) {
        console.warn('Cannot toggle feature: environmentFlag is undefined')
        return
      }
      const environmentId = environment.api_key

      try {
        if (environment.use_v2_feature_versioning) {
          // Versioned environment: use versioning API
          await createAndSetFeatureVersion({
            environmentId,
            featureId: flag.id,
            featureStates: [
              {
                ...environmentFlag,
                enabled: !environmentFlag.enabled,
              },
            ],
            projectId: flag.project,
          }).unwrap()
        } else {
          // Non-versioned environment: use simple PUT
          await updateFeatureState({
            body: {
              enabled: !environmentFlag.enabled,
            },
            environmentFlagId: environmentFlag.id,
            environmentId,
          }).unwrap()
        }

        if (options?.successMessage) {
          toast(options.successMessage)
        }
        options?.onSuccess?.()
      } catch (error: any) {
        const errorMessage =
          error?.data?.detail ||
          error?.message ||
          'Failed to toggle feature. Please try again.'
        console.error('Failed to toggle feature:', error, errorMessage)
        toast(options?.errorMessage || errorMessage, 'danger')
        options?.onError?.(error)
      }
    },
    [updateFeatureState, createAndSetFeatureVersion],
  )

  const isLoading = updateState.isLoading || versionState.isLoading

  return [toggleWithToast, { isLoading }] as const
}
