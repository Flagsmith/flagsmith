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
      organisationId: number,
      options?: UpdateOrganisationOptions,
    ) => {
      try {
        await updateOrganisation({
          body,
          id: organisationId,
        }).unwrap()
        toast(options?.successMessage || 'Saved organisation')
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
