import { FC } from 'react'
import { SegmentManagedBy } from 'common/types/responses'
import Tooltip from 'components/Tooltip'

const MANAGED_BY_LABELS: Record<SegmentManagedBy, string> = {
  '': 'Flagsmith',
  'cohort': 'a cohort',
  'dependency': 'a flag dependency',
  'experiment': 'an experiment',
  'release_pipeline': 'a gradual rollout',
}

type SystemSegmentOverrideLabelProps = {
  managedBy: SegmentManagedBy
}

const SystemSegmentOverrideLabel: FC<SystemSegmentOverrideLabelProps> = ({
  managedBy,
}) => (
  <Tooltip
    title={
      <div data-test='system-segment-override-label' className='chip chip--xs'>
        Managed by {MANAGED_BY_LABELS[managedBy]}
      </div>
    }
  >
    System segment overrides can't be changed here.
  </Tooltip>
)

export default SystemSegmentOverrideLabel
