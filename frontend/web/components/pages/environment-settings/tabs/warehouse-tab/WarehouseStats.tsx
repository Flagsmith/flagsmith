import React, { FC } from 'react'
import Icon from 'components/icons/Icon'

type WarehouseStatsProps = {
  errored: boolean
  lastEventReceived: string
  totalEventsReceived: number | null
  uniqueEventsCount: number | null
}

const formatCount = (value: number | null): string =>
  value !== null ? value.toLocaleString() : '-'

const WarehouseStats: FC<WarehouseStatsProps> = ({
  errored,
  lastEventReceived,
  totalEventsReceived,
  uniqueEventsCount,
}) => (
  <div className='d-flex flex-column gap-2'>
    {errored && (
      <div className='d-flex flex-row align-items-center gap-2 text-danger mb-2'>
        <Icon name='warning' width={14} fill='#EB5757' />
        <span>
          The connection is currently in error, please contact our team
        </span>
      </div>
    )}
    <div className='d-flex flex-row gap-2'>
      <span className='text-muted'>Last event received:</span>
      <span className='font-weight-medium'>{lastEventReceived}</span>
    </div>
    <div className='d-flex flex-row gap-2'>
      <span className='text-muted'>Total events received:</span>
      <span className='font-weight-medium'>
        {formatCount(totalEventsReceived)}
      </span>
    </div>
    <div className='d-flex flex-row gap-2'>
      <span className='text-muted'>Number of unique events:</span>
      <span className='font-weight-medium'>
        {formatCount(uniqueEventsCount)}
      </span>
    </div>
  </div>
)

WarehouseStats.displayName = 'WarehouseStats'
export default WarehouseStats
