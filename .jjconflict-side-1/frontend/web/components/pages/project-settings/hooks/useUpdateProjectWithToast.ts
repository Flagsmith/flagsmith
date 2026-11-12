import { useCallback } from 'react'
import { useUpdateProjectMutation } from 'common/services/useProject'
import { UpdateProjectBody } from 'common/types/requests'

type UpdateProjectOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
}

export const useUpdateProjectWithToast = () => {
  const [updateProject, state] = useUpdateProjectMutation()

  const updateWithToast = useCallback(
    async (
      body: UpdateProjectBody,
      projectId: number,
      options?: UpdateProjectOptions,
    ) => {
      try {
        await updateProject({
          body,
          id: projectId,
        }).unwrap()
        toast(options?.successMessage || 'Project Saved')
        // Refresh OrganisationStore to update navbar and other components
        // that rely on the legacy store
        AppActions.refreshOrganisation()
      } catch (error) {
        toast(
          options?.errorMessage ||
            'Failed to update setting. Please try again.',
          'danger',
        )
        options?.onError?.(error)
      }
    },
    [updateProject],
  )

  return [updateWithToast, state] as const
}
