import { createContext, useContext } from 'react'

const DropdownMenuContext = createContext<(() => void) | null>(null)

const noop = () => undefined

export const DropdownMenuCloseProvider = DropdownMenuContext.Provider
export const useCloseDropdownMenu = () =>
  useContext(DropdownMenuContext) ?? noop
