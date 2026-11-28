import AccountStore from 'common/stores/account-store'
import { AccountModel } from 'common/types/responses'
import useAccountStoreUpdates from './useAccountStoreUpdates'

export const getCurrentUser = (): AccountModel | undefined =>
  AccountStore.getUser() ?? undefined

export const useCurrentUser = (): AccountModel | undefined => {
  useAccountStoreUpdates()
  return getCurrentUser()
}
