import React, { FC, KeyboardEvent, ReactNode } from 'react'
import { colorIconDefault } from 'common/theme/tokens'
import Icon, { IconName } from './icons/Icon'
import Tooltip from './Tooltip'
import './StatItem.scss'

type VisibilityToggleProps = {
  colour: string
  isVisible: boolean
  onToggle: () => void
}

export type StatItemProps = {
  label: string
  value: string | number
  /** Qualifier under the value, e.g. "of 2M plan limit". */
  sub?: ReactNode
  /** State on the right of the label, e.g. a status badge. */
  badge?: ReactNode
  icon?: IconName
  // Optional: for displaying limits (e.g., "1,000 / 10,000")
  limit?: number | null
  // Optional: hover tooltip on the label
  tooltip?: string
  // Optional: for visibility toggle in charts
  visibilityToggle?: VisibilityToggleProps
}

const StatItem: FC<StatItemProps> = ({
  badge,
  icon,
  label,
  limit,
  sub,
  tooltip,
  value,
  visibilityToggle,
}) => {
  const formatNumber = (n: number) => n.toLocaleString()
  const formattedValue = typeof value === 'number' ? formatNumber(value) : value

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      visibilityToggle?.onToggle()
    }
  }

  return (
    <div className='stat-item'>
      <div className='stat-item__head'>
        {icon && (
          <Icon
            name={icon}
            width={16}
            fill={colorIconDefault}
            className='stat-item__icon'
          />
        )}
        <span className='stat-item__label'>
          {tooltip ? <Tooltip title={label}>{tooltip}</Tooltip> : label}
        </span>
        {badge && <span className='stat-item__badge'>{badge}</span>}
      </div>
      <div className='stat-item__value'>
        {formattedValue}
        {limit !== null && limit !== undefined && (
          <span className='stat-item__limit'> / {formatNumber(limit)}</span>
        )}
      </div>
      {sub && <div className='stat-item__sub'>{sub}</div>}
      {visibilityToggle && (
        <div
          role='checkbox'
          aria-checked={visibilityToggle.isVisible}
          aria-label={`Toggle ${label} visibility`}
          tabIndex={0}
          className='cursor-pointer d-flex align-items-center gap-2 mt-2'
          onClick={visibilityToggle.onToggle}
          onKeyDown={handleKeyDown}
        >
          <div
            className='visibility-checkbox'
            style={{ backgroundColor: visibilityToggle.colour }}
          >
            {visibilityToggle.isVisible && (
              <Icon name='checkmark' width={10} fill='white' />
            )}
          </div>
          <span className='text-muted fs-small'>Visible</span>
        </div>
      )}
    </div>
  )
}

export default StatItem
