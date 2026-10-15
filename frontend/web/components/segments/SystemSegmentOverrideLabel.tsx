import { FC } from 'react'
import { SegmentManagedBy } from 'common/types/responses'
import Tooltip from 'components/Tooltip'
import Button from 'components/base/forms/Button'

const MANAGED_BY_LABELS: Record<SegmentManagedBy, string> = {
  '': 'Flagsmith',
  'cohort': 'a cohort',
  'dependency': 'a flag dependency',
  'experiment': 'an experiment',
  'release_pipeline': 'a gradual rollout',
}

type SystemSegmentOverrideLabelProps = {
  managedBy: SegmentManagedBy
  projectId: number | string
  environmentId: string
  // Shows the flag's dependencies, where they can be changed.
  onViewDependencies?: () => void
}

const SystemSegmentOverrideLabel: FC<SystemSegmentOverrideLabelProps> = ({
  environmentId,
  managedBy,
  onViewDependencies,
  projectId,
}) => (
  <>
    <Tooltip
      title={
        <div
          data-test='system-segment-override-label'
          className='chip chip--xs ml-2'
        >
          Managed by {MANAGED_BY_LABELS[managedBy]}
        </div>
      }
    >
      System segment overrides can't be changed here.
    </Tooltip>
    {managedBy === 'dependency' && onViewDependencies && (
      <Button
        theme='text'
        size='xSmall'
        className='ml-2'
        onClick={onViewDependencies}
      >
        View dependencies
      </Button>
    )}
    {managedBy === 'experiment' && (
      <a
        className='ml-2 fs-small'
        href={`/project/${projectId}/environment/${environmentId}/experiments`}
      >
        View experiments
      </a>
    )}
  </>
)

export default SystemSegmentOverrideLabel
