import { FC } from 'react'
import { colorSurfaceAction, colorSurfaceEmphasis } from 'common/theme/tokens'
import Icon from 'components/icons/Icon'

// A prerequisite's state in this environment, shown as a toggle but read only.
const StateToggle: FC<{ isEnabled: boolean }> = ({ isEnabled }) => (
  <Icon
    name={isEnabled ? 'toggle-on' : 'toggle-off'}
    width={32}
    fill={isEnabled ? colorSurfaceAction : colorSurfaceEmphasis}
    role='img'
    aria-label={isEnabled ? 'On' : 'Off'}
  />
)

export default StateToggle
