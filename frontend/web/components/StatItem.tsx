import React, { FC, KeyboardEvent } from 'react'
import { colorIconDefault } from 'common/theme/tokens'
import Icon, { IconName } from './icons/Icon'
import Tooltip from './Tooltip'

type VisibilityToggleProps = {
  colour: string
  isVisible: boolean
  onToggle: () => void
}

export type StatItemProps = {
  icon: IconName
  label: string
  value: string | number
  // Optional: for displaying limits (e.g., "1,000 / 10,000")
  limit?: number | null
  // Optional: hover tooltip on the label
  tooltip?: string
  // Optional: for visibility toggle in charts
  visibilityToggle?: VisibilityToggleProps
}

const StatItem: FC<StatItemProps> = ({
  icon,
  label,
  limit,
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
    <div className='d-flex flex-row align-items-start gap-2'>
      <div className='plan-icon flex-shrink-0'>
        <Icon name={icon} width={32} fill={colorIconDefault} />
      </div>
      <div>
        <p className='fs-small lh-sm mb-0'>
          {tooltip ? <Tooltip title={label}>{tooltip}</Tooltip> : label}
        </p>
        <h4 className='mb-0'>
          {formattedValue}
          {limit !== null && limit !== undefined && (
            <span className='text-muted fs-small fw-normal'>
              {' '}
              / {formatNumber(limit)}
            </span>
          )}
        </h4>
        {visibilityToggle && (
          <div
            role='checkbox'
            aria-checked={visibilityToggle.isVisible}
            aria-label={`Toggle ${label} visibility`}
            tabIndex={0}
            className='cursor-pointer d-flex align-items-center gap-2 mt-1'
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
    </div>
  )
}

export default StatItem
