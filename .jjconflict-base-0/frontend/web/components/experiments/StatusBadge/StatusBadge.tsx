import { FC } from 'react'
import { ExperimentStatus } from 'common/types/responses'
import { EXPERIMENT_STATUS_LABELS } from 'components/experiments/constants'
import './StatusBadge.scss'

type StatusBadgeProps = {
  status: ExperimentStatus
}

const StatusBadge: FC<StatusBadgeProps> = ({ status }) => {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className='status-badge__dot' />
      {EXPERIMENT_STATUS_LABELS[status]}
    </span>
  )
}

export default StatusBadge
