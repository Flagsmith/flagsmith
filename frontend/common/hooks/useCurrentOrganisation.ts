import AccountStore from 'common/stores/account-store'
import { Organisation } from 'common/types/responses'
import useAccountStoreUpdates from './useAccountStoreUpdates'

export const getCurrentOrganisation = (): Organisation | undefined =>
  AccountStore.getOrganisation() ?? undefined

export const isOrganisationAdmin = (organisation?: Organisation): boolean =>
  organisation?.role === 'ADMIN'

export const useCurrentOrganisation = (): Organisation | undefined => {
  useAccountStoreUpdates()
  return getCurrentOrganisation()
}

export const useIsOrganisationAdmin = (): boolean =>
  isOrganisationAdmin(useCurrentOrganisation())
