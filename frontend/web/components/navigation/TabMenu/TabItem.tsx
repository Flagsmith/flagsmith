import { FC, ReactNode } from 'react'

type TabItemType = {
  /** @deprecated Only required when `tabLabel` is JSX and the parent `<Tabs>` uses the legacy `urlParam` prop for slug derivation. New consumers should pass a string `tabLabel` and use `useTabUrlSync` for URL persistence. */
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
