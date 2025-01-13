import React, { FC, FormEvent } from 'react'
import Tooltip from './Tooltip'
import UsersIcon from './svg/UsersIcon'

type IdentityOverridesIconType = {
  count: number | null
  showPlusIndicator?: boolean
  onClick?: (e: FormEvent) => void
}

const IdentityOverridesIcon: FC<IdentityOverridesIconType> = ({
  count,
  onClick,
  showPlusIndicator,
}) => {
  if (!count) {
    return null
  }
  const plusIndicatorText = showPlusIndicator ? '+' : ''
  return (
    <div onClick={onClick}>
      <Tooltip
        title={
          <span
            className='chip me-2 chip--xs bg-primary text-white'
            style={{ border: 'none' }}
          >
            <UsersIcon className='chip-svg-icon' />
            <span>
              {count}
              {plusIndicatorText}
            </span>
          </span>
        }
        place='top'
      >
        {`${count}${plusIndicatorText} Identity Override${
          count !== 1 || showPlusIndicator ? 's' : ''
        }`}
      </Tooltip>
    </div>
  )
}

export default IdentityOverridesIcon
