import React, { FC } from 'react'
import { Tag as TTag } from 'common/types/responses'
import Format from 'common/utils/format'
import Tooltip from 'components/Tooltip'
import OrganisationStore from 'common/stores/organisation-store'
import Utils from 'common/utils/utils'
import classNames from 'classnames'
import Icon, { IconName } from 'components/icons/Icon'
import {
  SYSTEM_TAG_UTILITIES,
  getTagSwatchUtilities,
  isSystemTag,
} from './tagSwatch'
type TagContent = {
  tag: Partial<TTag>
}
// Numeric-entity everything that is not alphanumeric or beyond Latin-1.
// Stated as the characters it keeps rather than the four ranges it escaped:
// the same set, without control characters in the literal.
function escapeHTML(unsafe: string) {
  return unsafe.replace(
    /[^0-9A-Za-z\u0100-\uFFFF]/g,
    (c) => `&#${`000${c.charCodeAt(0)}`.slice(-4)};`,
  )
}

const VCS_ICON_BY_LABEL: Record<string, IconName> = {
  'Issue Closed': 'issue-closed',
  'Issue Open': 'issue-linked',
  'PR Closed': 'pr-closed',
  'PR Dequeued': 'pr-dequeued',
  'PR Draft': 'pr-draft',
  'PR Merged': 'pr-merged',
  'PR Open': 'pr-linked',
}

const renderIcon = (
  tagType: string,
  tagLabel: string,
  isPermanent: boolean,
) => {
  switch (tagType) {
    case 'STALE':
      return <Icon name='stale' />
    case 'UNHEALTHY':
      return <Icon name='warning' width={16} />
    case 'GITHUB':
    case 'GITLAB': {
      const icon = VCS_ICON_BY_LABEL[tagLabel]
      return icon ? <Icon name={icon} /> : null
    }
    default:
      return isPermanent ? <Icon name='lock' width={16} /> : null
  }
}

const getTooltip = (tag: TTag | undefined) => {
  if (!tag) {
    return null
  }
  const stale_flags_limit_days = OrganisationStore.getProject(
    tag.project,
  )?.stale_flags_limit_days
  const disabled = Utils.tagDisabled(tag)
  const truncated = Format.truncateText(tag.label, 12)
  const isTruncated = truncated !== tag.label ? tag.label : null
  let tooltip = null
  switch (tag.type) {
    case 'STALE': {
      tooltip = `${
        disabled
          ? 'This feature is available with our <strong>Enterprise</strong> plan. '
          : ''
      }A feature is marked as stale if no changes have been made to it in any environment within ${stale_flags_limit_days} days. This is automatically applied and will be re-evaluated if you remove this tag unless you apply a permanent tag to the feature.`
      break
    }
    default:
      break
  }
  if (tag.is_permanent) {
    tooltip =
      'Features marked with this tag are not monitored for staleness and have deletion protection.'
  }
  if (isTruncated) {
    // Goes through dangerouslySetInnerHTML, so it cannot be a component. Same
    // classes as the real chip, so there is one set of colour rules.
    const utilities = isSystemTag(tag)
      ? SYSTEM_TAG_UTILITIES
      : `${getTagSwatchUtilities(tag.color)} border-0`
    return `<div>
        <span
          class="ds-chip ds-chip--xs d-inline-flex align-items-center rounded-md me-1 ${utilities}${
      disabled ? ' opacity-50' : ''
    }"
        >
          ${`${escapeHTML(tag.label)}`}
        </span>
          ${tooltip ?? ''}
      </div>`
  }
  return tooltip
}

const TagContent: FC<TagContent> = ({ tag }) => {
  const tagLabel = Format.truncateText(tag.label, 12)

  if (!tagLabel) {
    return null
  }

  const disabled = Utils.tagDisabled(tag)

  return (
    <Tooltip
      title={
        <span
          className={classNames('mr-1 flex-row align-items-center', {
            'opacity-50': disabled,
          })}
        >
          {tagLabel}
          {renderIcon(tag.type!, tag.label!, !!tag.is_permanent)}
        </span>
      }
    >
      {getTooltip(tag)}
    </Tooltip>
  )
}

export default TagContent
