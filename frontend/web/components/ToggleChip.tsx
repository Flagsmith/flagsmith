import React, { FC, ReactNode } from 'react'
import cx from 'classnames'
import Icon from './Icon'
import Utils from 'common/utils/utils'

export type ToggleChipProps = {
  color?: string
  active?: boolean
  onClick?: () => void
  className?: string
  children?: ReactNode
}

const ToggleChip: FC<ToggleChipProps> = ({
  active,
  children,
  className,
  color,
  onClick,
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
      className={cx('chip no-wrap mr-1 mt-0 clickable', className)}
    >
      <span
        style={{
          backgroundColor: active ? 'white' : 'transparent',
          border:
            active || !children ? 'none' : `1px solid ${colour.fade(0.76)}`,
        }}
        className={cx('icon-check', children ? 'mr-2' : null)}
      >
        {active && <Icon name='checkmark-square' fill={color} />}
      </span>
      {children}
    </Row>
  )
}

export default ToggleChip
