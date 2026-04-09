import React, { FC } from 'react'
import { ConnectionDetail } from 'components/warehouse/types'
import './ConnectionDetailsGrid.scss'

type ConnectionDetailsGridProps = {
  details: ConnectionDetail[]
}

const ConnectionDetailsGrid: FC<ConnectionDetailsGridProps> = ({ details }) => {
  return (
    <div className='wh-details-grid'>
      <span className='wh-details-grid__title'>Connection Details</span>
      <div className='wh-details-grid__rows'>
        {details.map((detail, index) => (
          <div
            key={detail.label}
            className={`wh-details-grid__row ${
              index < details.length - 1 ? 'wh-details-grid__row--bordered' : ''
            }`}
          >
            <span className='wh-details-grid__label'>{detail.label}</span>
            <span
              className={`wh-details-grid__value ${
                detail.masked ? 'wh-details-grid__value--masked' : ''
              }`}
            >
              {detail.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

ConnectionDetailsGrid.displayName = 'ConnectionDetailsGrid'
export default ConnectionDetailsGrid
