import React, { FC } from 'react'
import { Tag as TTag } from 'common/types/responses'
import color from 'color'
import Format from 'common/utils/format'
import { IonIcon } from '@ionic/react'
import { alarmOutline, lockClosed } from 'ionicons/icons'
import Tooltip from 'components/Tooltip'
import { getTagColor } from './Tag'
import OrganisationStore from 'common/stores/organisation-store'
type TagContent = {
  tag: Partial<TTag>
}

const getTooltip = (tag: TTag | undefined) => {
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
      tooltip = `A feature is marked as stale if no changes have been made to it in any environment within ${stale_flags_limit_days} days. This is automatically applied and will be re-evaluated if you remove this tag unless you apply a permanent tag to the feature.`
      break
    }
    default:
      break
  }
  if (tag.is_permanent) {
    tooltip =
      'Features marked with this tag are not monitored for staleness and have deletion protection.'
  }
  const tagColor = getTagColor(tag, false)

  if (isTruncated) {
    return `<div>
        <span
          style='background-color: ${color(tagColor).fade(
            0.92,
          )}; border: 1px solid ${color(tagColor).fade(0.76)}; color: ${color(
      tagColor,
    ).darken(0.1)};'
          class="chip d-inline-block chip--xs me-1"
        >
          ${tag.label}
        </span>
          ${tooltip || ''}
      </div>`
  }
  return tooltip
}

const TagContent: FC<TagContent> = ({ tag }) => {
  const tagLabel = Format.truncateText(tag.label, 12)

  if (!tagLabel) {
    return null
  }
  return (
    <Tooltip
      title={
        <span className={'mr-1 flex-row align-items-center'}>
          {tagLabel}
          {tag.type === 'STALE' ? (
            <IonIcon
              className='ms-1'
              icon={alarmOutline}
              color={color(tag.color).darken(0.1).string()}
            />
          ) : (
            tag.is_permanent && (
              <IonIcon
                className='ms-1'
                icon={lockClosed}
                color={color(tag.color).darken(0.1).string()}
              />
            )
          )}
        </span>
      }
    >
      {getTooltip(tag)}
    </Tooltip>
  )
}

export default TagContent
