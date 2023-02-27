import {FC, ReactNode} from 'react' // we need this to make JSX compile

type TabItemType = {
    tabLabel: ReactNode
    children: ReactNode
}

const TabItem: FC<TabItemType> = ({children}) => {
    return children || null as any
}

export default TabItem
