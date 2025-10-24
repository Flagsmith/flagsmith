import { FC, ReactNode } from 'react'

type TabItemType = {
  tabLabelString?: string
  tabLabel: ReactNode
  children: ReactNode
  className?: string
}

const TabItem: FC<TabItemType> = ({ children }) => {
  return children || (null as any)
}

export default TabItem
