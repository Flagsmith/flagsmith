import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip from 'components/base/Chip'
import TagContent from './TagContent'
import Constants from 'common/constants'
import {
  SYSTEM_TAG_UTILITIES,
  getTagSwatchUtilities,
  isSystemTag,
} from './tagSwatch'

type TagType = {
  className?: string
  // Whether the tag is unavailable to this organisation. The rule is a plan
  // entitlement, so it belongs to whoever knows about plans: see
  // Utils.tagDisabled. Reading it in here made a chip depend on AccountStore.
  disabled?: boolean
  // Partial, because `tag` is: the filter renders an "Untagged" pseudo-tag
  // with no id, and the create row previews a tag that does not exist yet.
  onClick?: (tag: Partial<TTag>) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

export const getTagColor = (tag: Partial<TTag>) => {
  if (tag.type === 'UNHEALTHY') {
    return Constants.featureHealth.unhealthyColor
  }
  return tag.color
}

const Tag: FC<TagType> = ({
  className,
  disabled = false,
  isDot,
  onClick,
  selected,
  tag,
}) => {
  if (isDot) {
    return (
      <div
        className={'tag--dot'}
        // No text on the dot, so the tag's own colour is safe here.
        style={{ backgroundColor: getTagColor(tag) }}
      />
    )
  }

  const isSystem = isSystemTag(tag)

  return (
    <Chip
      className={cx(
        // Legacy `.chip` carried margin-right; the primitive does not, so tags
        // keep it here or they butt against whatever follows.
        'me-1',
        isSystem
          ? SYSTEM_TAG_UTILITIES
          : getTagSwatchUtilities(getTagColor(tag)),
        { 'opacity-50': disabled },
        className,
      )}
      onClick={disabled || !onClick ? undefined : () => onClick(tag)}
      selected={selected}
      size='sm'
      variant='none'
    >
      <TagContent disabled={disabled} tag={tag} />
    </Chip>
  )
}

export default Tag
