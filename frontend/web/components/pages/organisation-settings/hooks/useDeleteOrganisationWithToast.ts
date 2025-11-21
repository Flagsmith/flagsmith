import { useCallback } from 'react'
import {
  useDeleteOrganisationMutation,
  useGetOrganisationsQuery,
} from 'common/services/useOrganisation'

type DeleteOrganisationOptions = {
  successMessage?: string
  errorMessage?: string
  onError?: (error: unknown) => void
  onSuccess?: (nextOrganisationId?: number) => void
}

export const useDeleteOrganisationWithToast = () => {
  const [deleteOrganisation, state] = useDeleteOrganisationMutation()
  const { data: organisations } = useGetOrganisationsQuery({})

  const deleteWithToast = useCallback(
    async (
      organisationId: string | number,
      options?: DeleteOrganisationOptions,
    ) => {
      try {
        await deleteOrganisation({
          id: String(organisationId),
        }).unwrap()

        // Calculate next available organisation after deletion
        const remaining = organisations?.results?.filter(
          (org) => org.id !== Number(organisationId),
        )
        const nextOrgId = remaining?.[0]?.id

        toast(options?.successMessage || 'Your organisation has been removed')
        options?.onSuccess?.(nextOrgId)
      } catch (error) {
        toast(
          options?.errorMessage ||
            'Failed to delete organisation. Please try again.',
          'danger',
        )
        options?.onError?.(error)
      }
    },
    [deleteOrganisation, organisations],
  )

  return [deleteWithToast, state] as const
}
