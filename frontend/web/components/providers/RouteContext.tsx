import React, { createContext, useContext } from 'react'

const RouteContext = createContext<RouteContextType>({})

type RouteContextType = {
  projectId?: number
  organisationId?: number
  environmentId?: string
}

export const RouteProvider: React.FC<{
  children: React.ReactNode
  value: RouteContextType
}> = ({ children, value }) => (
  <RouteContext.Provider value={value}>{children}</RouteContext.Provider>
)

export const useRouteContext = () => useContext(RouteContext)
