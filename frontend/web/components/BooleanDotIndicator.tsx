import React from 'react'
import ColorSwatch from './ColorSwatch'
import { colorIconAction, colorIconDisabled } from 'common/theme/tokens'

const BooleanDotIndicator = ({ enabled }: { enabled: boolean }) => (
  <ColorSwatch
    color={enabled ? colorIconAction : colorIconDisabled}
    shape='circle'
    size='lg'
  />
)

export default BooleanDotIndicator
