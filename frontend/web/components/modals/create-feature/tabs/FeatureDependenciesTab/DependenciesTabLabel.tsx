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
        <>
          {/* Read out in full instead, as part of the tab's name. The body's
          line height stops the chip taking the tab's, which is its height. */}
          <span aria-hidden className='ms-2 lh-base'>
            <Chip size='xs' variant={met < total ? 'warning' : 'neutral'}>
              {met}/{total}
            </Chip>
          </span>
          <span className='visually-hidden'>
            {met} of {total} prerequisites met
          </span>
        </>
      )}
    </>
  )
}

export default DependenciesTabLabel
