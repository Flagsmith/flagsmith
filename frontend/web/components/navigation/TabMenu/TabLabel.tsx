import { FC } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import { colorIconWarning } from 'common/theme/tokens'
import { TabItemProps } from './TabItem'

type TabLabelProps = Pick<TabItemProps, 'tabLabel' | 'isDirty'>

const TabLabel: FC<TabLabelProps> = ({ isDirty, tabLabel }) => (
  <>
    {tabLabel}
    {isDirty && (
      <span role='status' aria-label='Unsaved changes'>
        <ColorSwatch color={colorIconWarning} shape='circle' size='sm' />
      </span>
    )}
  </>
)

export default TabLabel
