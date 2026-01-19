import React, { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { checkmarkSharp } from 'ionicons/icons'
import Icon, { IconName } from './Icon'
import Utils from 'common/utils/utils'

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
  // Optional: for visibility toggle in charts
  visibilityToggle?: VisibilityToggleProps
}

const StatItem: FC<StatItemProps> = ({
  icon,
  label,
  limit,
  value,
  visibilityToggle,
}) => {
  const formattedValue =
    typeof value === 'number' ? Utils.numberWithCommas(value) : value

  return (
    <div className='d-flex flex-row align-items-start gap-2'>
      <div className='plan-icon flex-shrink-0'>
        <Icon name={icon} width={32} fill='#1A2634' />
      </div>
      <div>
        <p className='fs-small lh-sm mb-0'>{label}</p>
        <h4 className='mb-0'>
          {formattedValue}
          {limit !== null && limit !== undefined && (
            <span className='text-muted fs-small fw-normal'>
              {' '}
              / {Utils.numberWithCommas(limit)}
            </span>
          )}
        </h4>
        {visibilityToggle && (
          <div
            className='cursor-pointer d-flex align-items-center gap-2 mt-1'
            onClick={visibilityToggle.onToggle}
          >
            <div
              className='d-flex align-items-center justify-content-center text-white'
              style={{
                backgroundColor: visibilityToggle.colour,
                borderRadius: 2,
                flexShrink: 0,
                height: 16,
                width: 16,
              }}
            >
              {visibilityToggle.isVisible && (
                <IonIcon size={'8px'} color='white' icon={checkmarkSharp} />
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
