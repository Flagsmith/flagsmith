import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip from 'components/base/Chip'
import Utils from 'common/utils/utils'
import TagContent from './TagContent'
import Constants from 'common/constants'

type TagType = {
  className?: string
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

export const getTagColor = (tag: Partial<TTag>) =>
  tag.type === 'UNHEALTHY'
    ? Constants.featureHealth.unhealthyColor
    : tag.color ?? Constants.tagColors[0]

/** The colour the tag's dot is painted in: the hex on the record, as stored. */
export const tagDotColour = (tag: Partial<TTag>) => getTagColor(tag)

const Tag: FC<TagType> = ({ className, isDot, onClick, selected, tag }) => {
  if (isDot) {
    return (
      <div
        className={'tag--dot'}
        style={{ backgroundColor: tagDotColour(tag) }}
      />
    )
  }

  // Hide unhealthy tags if feature is disabled
  if (
    !Utils.getFlagsmithHasFeature('feature_health') &&
    tag.type === 'UNHEALTHY'
  ) {
    return null
  }

  const disabled = Utils.tagDisabled(tag)
  const isInteractive = !disabled && !!onClick

  return (
    <Chip
      // TagContent cuts the label at 12 characters, so a button named by its
      // content would read as the truncation.
      aria-label={isInteractive ? tag.label : undefined}
      className={cx('me-1', className)}
      dot={tagDotColour(tag)}
      onClick={isInteractive ? () => onClick?.(tag as TTag) : undefined}
      // A tag can be both chosen and out of plan, so the ring is not the
      // clickable state.
      selected={selected}
      size='sm'
    >
      <TagContent tag={tag} />
    </Chip>
  )
}

export default Tag
