import React, { FC } from 'react'

import Chip from 'components/base/Chip'

interface ControlWeightChipProps {
  percentage: number
}

// The control value's share of the variation split. The feature drawer and
// segment overrides both show it and had drifted apart: a chip in one, a
// hyphenated string in the other.
const ControlWeightChip: FC<ControlWeightChipProps> = ({ percentage }) => (
  <Chip variant='accent' size='xs'>
    {Math.max(0, percentage)}%
  </Chip>
)

export default ControlWeightChip
