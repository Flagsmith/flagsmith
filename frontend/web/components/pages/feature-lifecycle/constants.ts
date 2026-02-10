import type { IconName } from 'components/Icon'
import type { FilterState } from 'common/types/featureFilters'
import type { Section } from './types'
import { SortOrder } from 'common/types/requests'
import { TagStrategy } from 'common/types/responses'

export const DEFAULT_FILTER_STATE: FilterState = {
  group_owners: [],
  is_enabled: null,
  owners: [],
  search: null,
  showArchived: false,
  sort: { label: 'Name', sortBy: 'name', sortOrder: SortOrder.ASC },
  tag_strategy: TagStrategy.INTERSECTION,
  tags: [],
  value_search: '',
}

export const PERIOD_VALUES = [1, 7, 14, 30, 90]

function dayLabel(days: number): string {
  return days === 1 ? '1 day' : `${days} days`
}

export function buildPeriodOptions(prefix: string) {
  return PERIOD_VALUES.map((v) => ({
    label: `${prefix} ${dayLabel(v)}`,
    value: v,
  }))
}

export const STALE_TOOLTIP =
  'If no changes have been made to a feature in any environment within the configured threshold, the feature will be tagged as stale. You will need to enable feature versioning in your environments for stale features to be detected.'

export const MONITOR_TOOLTIP =
  'There could be several reasons:\n\n• Cached deployments — your application may still be running an older version that references this feature.\n• Not all repositories linked — code references scanning may not cover every repository that uses this feature.\n• Are you forcing users to use the latest version of your application? Older client versions may still evaluate this feature.'

export const SECTIONS: {
  key: Section
  icon: IconName
  label: string
  subtitle: string
  staleTooltip?: boolean
  monitorTooltip?: boolean
}[] = [
  {
    icon: 'rocket',
    key: 'new',
    label: 'New',
    subtitle: 'Recently created features with no code references yet.',
  },
  {
    icon: 'checkmark-circle',
    key: 'live',
    label: 'Live',
    subtitle:
      'Features with code references that are actively being evaluated.',
  },
  {
    icon: 'lock',
    key: 'permanent',
    label: 'Permanent',
    subtitle:
      'Features marked as permanent. These are not monitored for staleness and have deletion protection.',
  },
  {
    icon: 'clock',
    key: 'stale',
    label: 'Stale',
    staleTooltip: true,
    subtitle:
      'Features with code references that have been marked as stale. Candidates for code clean up.',
  },
  {
    icon: 'shield',
    key: 'monitor',
    label: 'Needs Monitoring',
    monitorTooltip: true,
    subtitle: 'No code references found but still receiving evaluations.',
  },
  {
    icon: 'trash-2',
    key: 'remove',
    label: 'To Remove',
    staleTooltip: true,
    subtitle: 'Stale flags with no code references and no evaluations.',
  },
]

export const excludeTag = (tag: {
  type: string
  is_permanent: boolean
}): boolean => tag.type === 'STALE' || tag.is_permanent
