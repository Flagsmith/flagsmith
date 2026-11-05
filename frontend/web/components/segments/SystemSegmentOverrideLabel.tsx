import { FC } from 'react'
import { SegmentManagedBy } from 'common/types/responses'
import Tooltip from 'components/Tooltip'
import Icon, { IconName } from 'components/icons/Icon'

const MANAGED_BY_LABELS: Record<SegmentManagedBy, string> = {
  '': 'Flagsmith',
  'cohort': 'a cohort',
  'dependency': 'a flag dependency',
  'experiment': 'an experiment',
  'release_pipeline': 'a gradual rollout',
}

// The icons the navigation uses for each, where it has one.
const MANAGED_BY_ICONS: Record<SegmentManagedBy, IconName> = {
  '': 'lock',
  'cohort': 'people',
  'dependency': 'layers',
  'experiment': 'flask',
  'release_pipeline': 'flash',
}

type SystemSegmentOverrideLabelProps = {
  managedBy: SegmentManagedBy
}

const SystemSegmentOverrideLabel: FC<SystemSegmentOverrideLabelProps> = ({
  managedBy,
}) => (
  <>
    <Icon name={MANAGED_BY_ICONS[managedBy]} width={16} fill='#9DA4AE' />
    <Tooltip
      title={
        <div
          data-test='system-segment-override-label'
          className='chip chip--xs ms-2'
        >
          Managed by {MANAGED_BY_LABELS[managedBy]}
        </div>
      }
    >
      System segment overrides can't be changed here.
    </Tooltip>
  </>
)

export default SystemSegmentOverrideLabel
