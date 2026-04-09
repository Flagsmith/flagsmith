import React, { FC } from 'react'
import { motion } from 'motion/react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import StatusBadge from 'components/experiments-v2/shared/StatusBadge'
import ConnectionDetailsGrid from './ConnectionDetailsGrid'
import {
  springBounce,
  badgeEntrance,
  staggerContainer,
  staggerItem,
} from 'common/utils/motion'
import { ConnectionDetail, ConnectionStats } from 'components/warehouse/types'
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
            <motion.div
              className='wh-connected__icon-box'
              variants={springBounce}
              initial='hidden'
              animate='visible'
            >
              <Icon name='flash' width={24} />
            </motion.div>
            <div className='wh-connected__name-col'>
              <span className='wh-connected__name'>Snowflake</span>
              <span className='wh-connected__account'>
                myorg.snowflakecomputing.com
              </span>
            </div>
          </div>
          <motion.div
            variants={badgeEntrance}
            initial='hidden'
            animate='visible'
          >
            <StatusBadge status='running' />
          </motion.div>
        </div>

        <div className='wh-connected__divider' />

        <motion.div
          className='wh-connected__stats'
          variants={staggerContainer(0.1)}
          initial='hidden'
          animate='visible'
        >
          <motion.div className='wh-connected__stat' variants={staggerItem}>
            <span className='wh-connected__stat-label'>
              Last Successful Delivery
            </span>
            <span className='wh-connected__stat-value'>
              {stats.lastDelivery}
            </span>
            <span className='wh-connected__stat-sub'>
              {stats.lastDeliveryDate}
            </span>
          </motion.div>
          <motion.div className='wh-connected__stat' variants={staggerItem}>
            <span className='wh-connected__stat-label'>
              Flag Evaluations (24h)
            </span>
            <span className='wh-connected__stat-value'>
              {stats.flagEvaluations24h.toLocaleString()}
            </span>
            <span className='wh-connected__stat-sub wh-connected__stat-sub--success'>
              {stats.flagEvaluationsTrend}
            </span>
          </motion.div>
          <motion.div className='wh-connected__stat' variants={staggerItem}>
            <span className='wh-connected__stat-label'>
              Custom Events (24h)
            </span>
            <span className='wh-connected__stat-value'>
              {stats.customEvents24h.toLocaleString()}
            </span>
            <span className='wh-connected__stat-sub wh-connected__stat-sub--success'>
              {stats.customEventsTrend}
            </span>
          </motion.div>
        </motion.div>
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
