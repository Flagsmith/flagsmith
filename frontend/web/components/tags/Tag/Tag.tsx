import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip, { ChipSize } from 'components/base/Chip'
import Constants from 'common/constants'
import TagContent from 'components/tags/TagContent'
import { tagChipColour } from 'components/tags/utils'

type TagType = {
  className?: string
  // A plan entitlement, not a UI state. See Utils.tagDisabled.
  disabled?: boolean
  onClick?: (tag: Partial<TTag>) => void
  selected?: boolean
  // Small where a tag labels something, md where it is the thing chosen.
  size?: ChipSize
  // Partial: the archived and untagged pseudo-tags have no id.
  tag: Partial<TTag>
}

// Here rather than utils: Constants would drag the app tree into the swatch test.
export const getTagColor = (tag: Partial<TTag>) =>
  tag.type === 'UNHEALTHY' ? Constants.featureHealth.unhealthyColor : tag.color

const Tag: FC<TagType> = ({
  className,
  disabled = false,
  onClick,
  selected,
  size = 'sm',
  tag,
}) => {
  const isInteractive = !disabled && !!onClick
  return (
    <Chip
      // TagContent cuts the label at 12 characters, so a button named by its
      // content would read as the truncation.
      aria-label={isInteractive ? tag.label : undefined}
      {...tagChipColour(tag)}
      className={cx('me-1', className)}
      onClick={isInteractive ? () => onClick?.(tag) : undefined}
      // A tag can be both chosen and out of plan, so the ring is not the
      // clickable state.
      selected={selected}
      size={size}
    >
      <TagContent disabled={disabled} tag={tag} />
    </Chip>
  )
}

export default Tag
