import React, { FC, FormEvent } from 'react'
import SegmentsIcon from './svg/SegmentsIcon'
import Tooltip from './Tooltip'

type SegmentOverridesIconType = {
  count: number | null
  onClick?: (e: FormEvent) => void
}

const SegmentOverridesIcon: FC<SegmentOverridesIconType> = ({
  count,
  onClick,
}) => {
  if (!count) {
    return null
  }
  return (
    <div onClick={onClick}>
      <Tooltip
        title={
          <span
            className='chip me-2 chip--xs bg-primary text-white'
            style={{ border: 'none' }}
          >
            <SegmentsIcon className='chip-svg-icon' />
            <span>{count}</span>
          </span>
        }
        place='top'
      >
        {`${count} Segment Override${count !== 1 ? 's' : ''}`}
      </Tooltip>
    </div>
  )
}

export default SegmentOverridesIcon
