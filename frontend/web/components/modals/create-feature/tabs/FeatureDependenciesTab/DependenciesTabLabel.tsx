import { FC } from 'react'
import Chip from 'components/base/Chip'
import { PrerequisiteRow, countMet } from './prerequisiteState'

type DependenciesTabLabelProps = {
  // Undefined while loading, when there's nothing to count yet.
  prerequisites?: PrerequisiteRow[]
}

// Counts the prerequisites met, as the flag is served off while any isn't.
const DependenciesTabLabel: FC<DependenciesTabLabelProps> = ({
  prerequisites,
}) => {
  const { met, total } = countMet(prerequisites ?? [])
  return (
    <>
      Dependencies
      {!!total && (
        <span
          data-test='dependencies-met-count'
          aria-label={`${met} of ${total} prerequisites met`}
          className='ms-2'
        >
          <Chip size='xs' variant={met < total ? 'warning' : 'neutral'}>
            {met}/{total}
          </Chip>
        </span>
      )}
    </>
  )
}

export default DependenciesTabLabel
