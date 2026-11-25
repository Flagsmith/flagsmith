import { createContext, useContext } from 'react'

// Lets an item close its menu even when its handler stops the click
const DropdownMenuContext = createContext<() => void>(() => undefined)

export const DropdownMenuCloseProvider = DropdownMenuContext.Provider
export const useCloseDropdownMenu = () => useContext(DropdownMenuContext)
