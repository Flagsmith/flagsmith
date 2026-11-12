import { FC } from 'react'
import { SegmentManagedBy } from 'common/types/responses'
import Tooltip from 'components/Tooltip'
import Icon, { IconName } from 'components/icons/Icon'
import Chip from 'components/base/Chip'
import { colorIconSecondary } from 'common/theme/tokens'

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
    <Icon
      name={MANAGED_BY_ICONS[managedBy]}
      width={16}
      fill={colorIconSecondary}
    />
    <Tooltip
      title={
        <Chip size='xs' className='ms-2'>
          Managed by {MANAGED_BY_LABELS[managedBy]}
        </Chip>
      }
    >
      System segment overrides can't be changed here.
    </Tooltip>
  </>
)

export default SystemSegmentOverrideLabel
