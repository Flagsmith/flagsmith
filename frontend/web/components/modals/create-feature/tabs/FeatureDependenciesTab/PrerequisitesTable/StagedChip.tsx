import { FC } from 'react'
import { StagedAction } from 'common/types/responses'
import Chip, { ChipVariant } from 'components/base/Chip'

type StagedChipProps = {
  action: StagedAction
  isRefused?: boolean
}

const variant = (action: StagedAction, isRefused?: boolean): ChipVariant => {
  if (isRefused) return 'danger'
  return action === 'add' ? 'accent' : 'neutral'
}

const StagedChip: FC<StagedChipProps> = ({ action, isRefused }) => (
  <Chip
    size='xs'
    variant={variant(action, isRefused)}
    className='flex-shrink-0'
  >
    {isRefused ? 'Rejected' : 'Staged'}: {action}
  </Chip>
)

export default StagedChip
