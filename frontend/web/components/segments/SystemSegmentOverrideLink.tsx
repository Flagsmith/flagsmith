import { FC } from 'react'
import { SegmentManagedBy } from 'common/types/responses'
import Button from 'components/base/forms/Button'

type SystemSegmentOverrideLinkProps = {
  managedBy: SegmentManagedBy
  projectId: number | string
  environmentId: string
  // Shows the flag's dependencies, where they can be changed.
  onViewDependencies?: () => void
}

// Links a system segment override to what manages it, where there's a page
// for it. Styled as the actions button of other segment overrides.
const SystemSegmentOverrideLink: FC<SystemSegmentOverrideLinkProps> = ({
  environmentId,
  managedBy,
  onViewDependencies,
  projectId,
}) => {
  if (managedBy === 'dependency' && onViewDependencies) {
    return (
      <Button theme='secondary' size='small' onClick={onViewDependencies}>
        View dependencies
      </Button>
    )
  }
  if (managedBy === 'experiment') {
    return (
      <Button
        theme='secondary'
        size='small'
        href={`/project/${projectId}/environment/${environmentId}/experiments`}
      >
        View experiments
      </Button>
    )
  }
  return null
}

export default SystemSegmentOverrideLink
