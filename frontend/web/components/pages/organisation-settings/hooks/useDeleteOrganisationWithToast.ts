import { useCallback } from 'react'
import {
  useDeleteOrganisationMutation,
  useGetOrganisationsQuery,
} from 'common/services/useOrganisation'
import AppActions from 'common/dispatcher/app-actions'

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
    async (organisationId: number, options?: DeleteOrganisationOptions) => {
      try {
        await deleteOrganisation({
          id: organisationId,
        }).unwrap()

        const nextOrgId = organisations?.results?.filter(
          (org) => org.id !== organisationId,
        )?.[0]?.id

        AppActions.selectOrganisation(nextOrgId)
        AppActions.getOrganisation(nextOrgId)

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
