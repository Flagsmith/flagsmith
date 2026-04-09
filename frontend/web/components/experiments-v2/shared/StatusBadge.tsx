import React, { FC } from 'react'
import { ExperimentStatus } from 'components/experiments-v2/types'
import './StatusBadge.scss'

type StatusBadgeProps = {
  status: ExperimentStatus
}

const STATUS_LABELS: Record<ExperimentStatus, string> = {
  completed: 'Completed',
  paused: 'Paused',
  running: 'Running',
}

const StatusBadge: FC<StatusBadgeProps> = ({ status }) => {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className='status-badge__dot' />
      {STATUS_LABELS[status]}
    </span>
  )
}

StatusBadge.displayName = 'StatusBadge'
export default StatusBadge
