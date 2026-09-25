import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip from 'components/base/Chip'
import Utils from 'common/utils/utils'
import TagContent from './TagContent'
import Constants from 'common/constants'
import {
  SYSTEM_TAG_UTILITIES,
  getTagSwatchUtilities,
  isSystemTag,
} from './tagSwatch'

type TagType = {
  className?: string
  onClick?: (tag: TTag) => void
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

const Tag: FC<TagType> = ({ className, isDot, onClick, selected, tag }) => {
  if (isDot) {
    return (
      <div
        className={'tag--dot'}
        // No text on the dot, so the tag's own colour is safe here.
        style={{ backgroundColor: getTagColor(tag) }}
      />
    )
  }

  // Hide unhealthy tags if feature is disabled. This used to sit below the
  // toggle branch, so a clickable tag skipped it.
  if (
    !Utils.getFlagsmithHasFeature('feature_health') &&
    tag.type === 'UNHEALTHY'
  ) {
    return null
  }

  const disabled = Utils.tagDisabled(tag)
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
        // Every tag keeps its border. The Content fills are faint by design,
        // 1.14 to 1.59 against the light page, so the edge is what makes a tag
        // read as a tag. Prod does the same: a faded fill with a stronger
        // border, and his own banners pair a 100 fill with a 500 border.
        { 'opacity-50': disabled },
        className,
      )}
      onClick={disabled || !onClick ? undefined : () => onClick(tag as TTag)}
      selected={selected}
      variant='none'
    >
      <TagContent tag={tag} />
    </Chip>
  )
}

export default Tag
