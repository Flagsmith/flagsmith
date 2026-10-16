import { FC } from 'react'
import Constants from 'common/constants'
import Icon from 'components/icons/Icon'
import Link from 'components/base/link'
import Tooltip from 'components/Tooltip'

// Flag dependencies have no docs page of their own yet, so this points at the
// nearest one that exists.
const DEPENDENCIES_DOCS_URL =
  'https://docs.flagsmith.com/basic-features/managing-features'

type DependenciesHeaderProps = {
  isPrerequisite: boolean
}

const DependenciesHeader: FC<DependenciesHeaderProps> = ({
  isPrerequisite,
}) => (
  <>
    <div className='d-flex mb-2'>
      <Tooltip
        title={
          <h5 className='mb-0'>
            Flag dependencies <Icon name='info-outlined' />
          </h5>
        }
        place='top'
      >
        {Constants.strings.FEATURE_DEPENDENCIES_DESCRIPTION}
      </Tooltip>
    </div>

    {/* The rule cannot apply to a flag that cannot have prerequisites, so
        the empty state explains that case instead. */}
    {!isPrerequisite && (
      <div className='text-muted mb-3'>
        This flag only serves its own value when every prerequisite below is on.{' '}
        <Link href={DEPENDENCIES_DOCS_URL} target='_blank'>
          Learn more
        </Link>
      </div>
    )}
  </>
)

export default DependenciesHeader
