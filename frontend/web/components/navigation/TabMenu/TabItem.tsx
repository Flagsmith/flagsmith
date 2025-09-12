import { FC, ReactNode } from 'react' // we need this to make JSX compile

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
