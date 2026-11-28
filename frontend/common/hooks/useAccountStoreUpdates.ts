import { useSyncExternalStore } from 'react'
import AccountStore from 'common/stores/account-store'

// Bumped on every store change, so React can tell a change happened between
// render and subscribe. Counted from the first render, not at import, so
// tests that mock the store can still load this module.
let version = 0
let counting = false
const countChanges = () => {
  if (counting) return
  counting = true
  AccountStore.on('change', () => {
    version += 1
  })
}

const subscribe = (onChange: () => void) => {
  AccountStore.on('change', onChange)
  return () => {
    AccountStore.off('change', onChange)
  }
}

const getVersion = () => version

// Re-renders the caller whenever the legacy account store changes.
const useAccountStoreUpdates = () => {
  countChanges()
  useSyncExternalStore(subscribe, getVersion)
}

export default useAccountStoreUpdates
