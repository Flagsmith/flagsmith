import { useCallback } from 'react'
import { useRemoveProjectFlagMutation } from 'common/services/useProjectFlag'
import type { ProjectFlag } from 'common/types/responses'

type RemoveFeatureOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
  onSuccess?: () => void
}

/** Removes a feature flag with toast notifications. */
export const useRemoveFeatureWithToast = () => {
  const [removeProjectFlag, state] = useRemoveProjectFlagMutation()

  const removeWithToast = useCallback(
    async (
      projectFlag: ProjectFlag,
      projectId: number,
      options?: RemoveFeatureOptions,
    ) => {
      try {
        await removeProjectFlag({
          flag_id: projectFlag.id,
          project_id: projectId,
        }).unwrap()

        toast(options?.successMessage || `Removed feature: ${projectFlag.name}`)
        options?.onSuccess?.()
      } catch (error) {
        console.error('Failed to remove feature:', error)
        toast(
          options?.errorMessage ||
            'Failed to remove feature. Please try again.',
          'danger',
        )
        options?.onError?.(error)
      }
    },
    [removeProjectFlag],
  )

  return [removeWithToast, state] as const
}
