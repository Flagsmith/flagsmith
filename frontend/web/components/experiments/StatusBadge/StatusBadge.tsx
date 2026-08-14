import { FC } from 'react'
import Chip, { ChipDot, ChipVariant } from 'components/base/Chip'
import { ExperimentStatus } from 'common/types/responses'
import { EXPERIMENT_STATUS_LABELS } from 'components/experiments/constants'

const STATUS_VARIANTS: Record<ExperimentStatus, ChipVariant> = {
  completed: 'muted',
  created: 'info',
  paused: 'warning',
  running: 'success',
}

type StatusBadgeProps = {
  status: ExperimentStatus
}

const StatusBadge: FC<StatusBadgeProps> = ({ status }) => (
  <Chip variant={STATUS_VARIANTS[status]} size='sm' pill>
    <ChipDot />
    {EXPERIMENT_STATUS_LABELS[status]}
  </Chip>
)

export default StatusBadge
