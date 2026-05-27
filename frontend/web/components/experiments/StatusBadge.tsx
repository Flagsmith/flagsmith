import { FC } from 'react'
import { ExperimentStatus } from 'common/types/responses'
import './StatusBadge.scss'

const STATUS_LABELS: Record<ExperimentStatus, string> = {
  completed: 'Completed',
  created: 'Created',
  paused: 'Paused',
  running: 'Running',
}

type StatusBadgeProps = {
  status: ExperimentStatus
}

const StatusBadge: FC<StatusBadgeProps> = ({ status }) => {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className='status-badge__dot' />
      {STATUS_LABELS[status]}
    </span>
  )
}

export default StatusBadge
