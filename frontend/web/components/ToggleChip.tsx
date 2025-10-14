import React, { FC, ReactNode } from 'react'
import cx from 'classnames'
import Icon from './Icon'
import Utils from 'common/utils/utils'

type ToggleChipProps = {
  color?: string
  active?: boolean
  onClick?: () => void
  className?: string
  size?: 'xSmall' | 'small' | 'medium' | 'large'
  children?: ReactNode
}

const ToggleChip: FC<ToggleChipProps> = ({
  active,
  children,
  className,
  color,
  onClick,
  size,
}) => {
  const colour = Utils.colour(color)
  return (
    <Row
      style={
        color
          ? {
              backgroundColor: children ? colour.fade(0.92) : colour.fade(0.76),
              border: `1px solid ${colour.fade(0.76)}`,
              color: colour.darken(0.1),
            }
          : undefined
      }
      onClick={onClick}
      className={cx(
        'chip no-wrap mr-1 mt-0 clickable',
        size && `chip--${size}`,
        className,
      )}
    >
      <span
        style={{
          backgroundColor: active ? 'white' : 'transparent',
          border:
            active || !children ? 'none' : `1px solid ${colour.fade(0.76)}`,
          marginRight: children ? '0.5rem' : '0',
        }}
        className='icon-check'
      >
        {active && <Icon width={14} name='checkmark-square' fill={color} />}
      </span>
      {children}
    </Row>
  )
}

export default ToggleChip
