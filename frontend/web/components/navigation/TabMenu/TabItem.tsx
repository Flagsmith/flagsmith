import { FC, ReactNode } from 'react'

export type TabItemProps = {
  tabLabelString?: string
  tabLabel: ReactNode
  children: ReactNode
  className?: string
  // Renders an unsaved-changes badge next to the label. Lifted out of consumers
  // so positioning lives in one place and TabButton can wrap label + badge in
  // a flex container that prevents the badge from breaking onto a new line.
  isDirty?: boolean
  'data-test'?: string
  id?: string
}

const TabItem: FC<TabItemProps> = ({ children }) => {
  return children || (null as any)
}

export default TabItem
