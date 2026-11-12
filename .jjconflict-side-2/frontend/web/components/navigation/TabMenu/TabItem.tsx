import { FC, ReactNode } from 'react'

type TabItemType = {
  tabLabelString?: string
  tabLabel: ReactNode
  children: ReactNode
  className?: string
  // Renders an unsaved-changes badge next to the label. Lifted out of consumers
  // so positioning lives in one place and TabButton can wrap label + badge in
  // a flex container that prevents the badge from breaking onto a new line.
  isDirty?: boolean
}

const TabItem: FC<TabItemType> = ({ children }) => {
  return children || (null as any)
}

export default TabItem
