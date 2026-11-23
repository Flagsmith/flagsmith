import { FC } from 'react'
import VariantName from 'components/experiments/results/VariantName'
import { formatChancePct } from 'components/experiments/results/derive'
import { VariantChoice } from './utils'

type VariantChoiceRowProps = {
  choice: VariantChoice
}

const VariantChoiceRow: FC<VariantChoiceRowProps> = ({ choice }) => (
  <div className='d-flex align-items-center gap-2'>
    <VariantName colour={choice.colour} name={choice.name} />
    <code
      className='text-truncate'
      style={{ minWidth: 0 }}
      title={choice.value}
    >
      {choice.value}
    </code>
    {choice.chanceToWin !== null && (
      <span className='ms-auto flex-shrink-0 text-secondary fs-caption'>
        {formatChancePct(choice.chanceToWin)} chance to win
      </span>
    )}
  </div>
)

export default VariantChoiceRow
