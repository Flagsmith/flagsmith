import { useEffect, useReducer } from 'react'
import AccountStore from 'common/stores/account-store'

// Re-renders the caller whenever the legacy account store changes.
const useAccountStoreUpdates = () => {
  const [, rerender] = useReducer((count: number) => count + 1, 0)
  useEffect(() => {
    AccountStore.on('change', rerender)
    return () => {
      AccountStore.off('change', rerender)
    }
  }, [])
}

export default useAccountStoreUpdates
