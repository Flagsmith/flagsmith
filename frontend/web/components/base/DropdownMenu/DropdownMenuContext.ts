import { createContext, useContext } from 'react'

// Holds the menu's close; null outside a menu
const DropdownMenuContext = createContext<(() => void) | null>(null)

const noop = () => undefined

export const DropdownMenuCloseProvider = DropdownMenuContext.Provider
export const useCloseDropdownMenu = () =>
  useContext(DropdownMenuContext) ?? noop
