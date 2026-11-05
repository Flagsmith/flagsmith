import { FC } from 'react'
import cn from 'classnames'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'

// Whether a prerequisite is in the state the feature needs. Undefined where
// the rule cannot be read.
const Satisfies: FC<{ isMet?: boolean }> = ({ isMet }) => {
  if (isMet === undefined) {
    return (
      <Tooltip
        title={
          <span
            className='d-inline-flex align-items-center gap-1 text-secondary'
            role='img'
            aria-label='Unknown'
          >
            <Icon name='info-outlined' width={16} />
          </span>
        }
        place='top'
      >
        This comes from a segment you wrote, so Flagsmith cannot tell which
        state it expects.
      </Tooltip>
    )
  }
  return (
    <span
      className={cn(
        'd-inline-flex align-items-center gap-1',
        isMet ? 'text-success' : 'text-secondary',
      )}
    >
      <Icon name={isMet ? 'checkmark-circle' : 'minus-circle'} width={16} />
      {isMet ? 'Yes' : 'No'}
    </span>
  )
}

export default Satisfies
