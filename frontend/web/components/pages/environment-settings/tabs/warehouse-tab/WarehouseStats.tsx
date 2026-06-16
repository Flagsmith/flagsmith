import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import Skeleton from 'components/Skeleton'

type WarehouseStatsProps = {
  errored: boolean
  lastEventReceived: string
  totalEventsReceived: number | null
  uniqueEventsCount: number | null
  loading?: boolean
}

const formatCount = (value: number | null): string =>
  value !== null ? value.toLocaleString() : '-'

const StatValue: FC<{ value: number | null; loading?: boolean }> = ({
  loading,
  value,
}) =>
  loading && value === null ? (
    <Skeleton variant='text' width={56} height={14} />
  ) : (
    <span className='font-weight-medium'>{formatCount(value)}</span>
  )

const WarehouseStats: FC<WarehouseStatsProps> = ({
  errored,
  lastEventReceived,
  loading,
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
    <div className='d-flex flex-row align-items-center gap-2'>
      <span className='text-muted'>Total events received:</span>
      <StatValue loading={loading} value={totalEventsReceived} />
    </div>
    <div className='d-flex flex-row align-items-center gap-2'>
      <span className='text-muted'>Number of unique events:</span>
      <StatValue loading={loading} value={uniqueEventsCount} />
    </div>
  </div>
)

WarehouseStats.displayName = 'WarehouseStats'
export default WarehouseStats
