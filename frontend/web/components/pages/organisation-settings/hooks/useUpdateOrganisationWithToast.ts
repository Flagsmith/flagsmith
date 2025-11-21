import { useCallback } from 'react'
import { useUpdateOrganisationMutation } from 'common/services/useOrganisation'
import { UpdateOrganisationBody } from 'common/types/requests'

type UpdateOrganisationOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
}

export const useUpdateOrganisationWithToast = () => {
  const [updateOrganisation, state] = useUpdateOrganisationMutation()

  const updateWithToast = useCallback(
    async (
      body: UpdateOrganisationBody,
      organisationId: string | number,
      options?: UpdateOrganisationOptions,
    ) => {
      try {
        await updateOrganisation({
          body,
          id: String(organisationId),
        }).unwrap()
        toast(options?.successMessage || 'Organisation updated')
        // Refresh AccountStore to update navbar and other components
        // that rely on the legacy store
        AppActions.refreshOrganisation()
      } catch (error) {
        toast(
          options?.errorMessage ||
            'Failed to update organisation. Please try again.',
          'danger',
        )
        options?.onError?.(error)
      }
    },
    [updateOrganisation],
  )

  return [updateWithToast, state] as const
}
