import { Tag as TTag } from 'common/types/responses'

/** Applied by the system rather than picked: stale, unhealthy, GitHub, GitLab. */
export const isSystemTag = (tag: Partial<TTag>): boolean =>
  !!tag.type && tag.type !== 'NONE'

// Its state is in the icon, so it keeps the plain surface rather than a hue.
export const SYSTEM_TAG_UTILITIES = 'bg-surface-default text-default'
