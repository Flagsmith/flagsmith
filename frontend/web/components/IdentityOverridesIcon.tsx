import React, { FC, FormEvent } from 'react'
import SegmentsIcon from './svg/SegmentsIcon'
import Tooltip from './Tooltip'
import UsersIcon from './svg/UsersIcon'

type IdentityOverridesIconType = {
  count: number | null
  onClick?: (e: FormEvent) => void
}

const IdentityOverridesIcon: FC<IdentityOverridesIconType> = ({
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
            <UsersIcon className='chip-svg-icon' />
            <span>{count}</span>
          </span>
        }
        place='top'
      >
        {`${count} Identity Override${count !== 1 ? 's' : ''}`}
      </Tooltip>
    </div>
  )
}

export default IdentityOverridesIcon
