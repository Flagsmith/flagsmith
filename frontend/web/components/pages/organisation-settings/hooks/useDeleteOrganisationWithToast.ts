import { useCallback } from 'react'
import { useDeleteOrganisationMutation } from 'common/services/useOrganisation'

type DeleteOrganisationOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
  onSuccess?: () => void
}

export const useDeleteOrganisationWithToast = () => {
  const [deleteOrganisation, state] = useDeleteOrganisationMutation()

  const deleteWithToast = useCallback(
    async (
      organisationId: string | number,
      options?: DeleteOrganisationOptions,
    ) => {
      try {
        await deleteOrganisation({
          id: String(organisationId),
        }).unwrap()
        toast(options?.successMessage || 'Your organisation has been removed')
        options?.onSuccess?.()
      } catch (error) {
        toast(
          options?.errorMessage ||
            'Failed to delete organisation. Please try again.',
          'danger',
        )
        options?.onError?.(error)
      }
    },
    [deleteOrganisation],
  )

  return [deleteWithToast, state] as const
}
