import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import StatusBadge from 'components/experiments-v2/shared/StatusBadge'
import ConnectionDetailsGrid from './ConnectionDetailsGrid'
import {
  ConnectionDetail,
  ConnectionStats,
  MOCK_CONFIG,
} from 'components/warehouse/types'
import './ConnectedState.scss'

type ConnectedStateProps = {
  stats: ConnectionStats
  details: ConnectionDetail[]
  onEdit: () => void
  onDisconnect: () => void
}

const ConnectedState: FC<ConnectedStateProps> = ({
  details,
  onDisconnect,
  onEdit,
  stats,
}) => {
  return (
    <div className='wh-connected'>
      {/* Status card */}
      <div className='wh-connected__status-card'>
        <div className='wh-connected__status-top'>
          <div className='wh-connected__info'>
            <div className='wh-connected__icon-box'>
              <Icon name='flash' width={24} />
            </div>
            <div className='wh-connected__name-col'>
              <span className='wh-connected__name'>Snowflake</span>
              <span className='wh-connected__account'>
                {MOCK_CONFIG.accountIdentifier}
              </span>
            </div>
          </div>
          <StatusBadge status='running' />
        </div>

        <div className='wh-connected__divider' />

        <div className='wh-connected__stats'>
          <div className='wh-connected__stat'>
            <span className='wh-connected__stat-label'>
              Last Successful Delivery
            </span>
            <span className='wh-connected__stat-value'>
              {stats.lastDelivery}
            </span>
            <span className='wh-connected__stat-sub'>
              {stats.lastDeliveryDate}
            </span>
          </div>
          <div className='wh-connected__stat'>
            <span className='wh-connected__stat-label'>
              Flag Evaluations (24h)
            </span>
            <span className='wh-connected__stat-value'>
              {stats.flagEvaluations24h.toLocaleString()}
            </span>
            <span className='wh-connected__stat-sub wh-connected__stat-sub--success'>
              {stats.flagEvaluationsTrend}
            </span>
          </div>
          <div className='wh-connected__stat'>
            <span className='wh-connected__stat-label'>
              Custom Events (24h)
            </span>
            <span className='wh-connected__stat-value'>
              {stats.customEvents24h.toLocaleString()}
            </span>
            <span className='wh-connected__stat-sub wh-connected__stat-sub--success'>
              {stats.customEventsTrend}
            </span>
          </div>
        </div>
      </div>

      {/* Connection details */}
      <ConnectionDetailsGrid details={details} />

      {/* Actions */}
      <div className='wh-connected__actions'>
        <Button
          theme='outline'
          size='small'
          iconLeft='edit'
          iconSize={14}
          onClick={onEdit}
        >
          Edit Connection
        </Button>
        <Button theme='danger' size='small' onClick={onDisconnect}>
          Disconnect
        </Button>
      </div>
    </div>
  )
}

ConnectedState.displayName = 'WarehouseConnectedState'
export default ConnectedState
