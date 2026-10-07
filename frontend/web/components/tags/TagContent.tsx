import React, { FC } from 'react'
import { Tag as TTag } from 'common/types/responses'
import Format from 'common/utils/format'
import Tooltip from 'components/Tooltip'
import OrganisationStore from 'common/stores/organisation-store'
import classNames from 'classnames'
import Icon, { IconName } from 'components/icons/Icon'
import { tagChipHtml } from './utils'

type TagContentProps = {
  disabled?: boolean
  tag: Partial<TTag>
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

const renderIcon = (tag: Partial<TTag>) => {
  switch (tag.type) {
    case 'STALE':
      return <Icon name='stale' />
    case 'UNHEALTHY':
      return <Icon name='warning' width={16} />
    case 'GITHUB':
    case 'GITLAB': {
      const icon = VCS_ICON_BY_LABEL[tag.label ?? '']
      return icon ? <Icon name={icon} /> : null
    }
    default:
      // Outline at 12px: a padlock heavier than its label reads as a sticker.
      return tag.is_permanent ? <Icon name='lock-outline' width={12} /> : null
  }
}

const getTooltip = (tag: Partial<TTag>, disabled: boolean) => {
  if (!tag) {
    return null
  }
  const stale_flags_limit_days = OrganisationStore.getProject(
    tag.project,
  )?.stale_flags_limit_days
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
    return `<div>${tagChipHtml(tag, { className: 'me-1', disabled })}${
      tooltip ?? ''
    }</div>`
  }
  return tooltip
}

const TagContent: FC<TagContentProps> = ({ disabled = false, tag }) => {
  const tagLabel = Format.truncateText(tag.label, 12)

  if (!tagLabel) {
    return null
  }

  return (
    <Tooltip
      title={
        // The only fade: TableTagFilter renders this without a Tag around it,
        // and two of them compound to 25%.
        <span
          className={classNames('gap-1 flex-row', {
            'opacity-50': disabled,
          })}
        >
          {tagLabel}
          {renderIcon(tag)}
        </span>
      }
    >
      {getTooltip(tag, disabled)}
    </Tooltip>
  )
}

export default TagContent
