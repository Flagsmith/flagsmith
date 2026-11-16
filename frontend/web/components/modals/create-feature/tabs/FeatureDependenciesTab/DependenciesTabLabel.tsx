import { FC } from 'react'
import cn from 'classnames'
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
          className={cn(
            'ms-2 px-2 border rounded-sm fs-small lh-sm',
            met < total
              ? 'bg-surface-warning text-warning border-warning'
              : 'bg-surface-muted text-secondary border-default',
          )}
        >
          {met}/{total}
        </span>
      )}
    </>
  )
}

export default DependenciesTabLabel
