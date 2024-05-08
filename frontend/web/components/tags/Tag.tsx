import React, { FC } from 'react'
import color from 'color'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import TagContent from './TagContent'

type TagType = {
  className?: string
  hideNames?: boolean
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

export const getTagColor = (tag: Partial<TTag>, selected?: boolean) => {
  if (Utils.getFlagsmithHasFeature('dark_mode') && tag.color === '#344562') {
    return '#9DA4AE'
  }
  if (selected) {
    return tag.color
  }
  return tag.color
}

const Tag: FC<TagType> = ({
  className,
  hideNames,
  isDot,
  onClick,
  selected,
  tag,
}) => {
  const tagColor = getTagColor(tag, selected)
  if (isDot) {
    return (
      <div
        className={'tag--dot'}
        style={{
          backgroundColor: `${color(tagColor).darken(0.1)}`,
        }}
      />
    )
  }

  const disabled = Utils.tagDisabled(tag)

  if (!hideNames && !!onClick) {
    return (
      <ToggleChip
        color={tagColor}
        active={selected}
        onClick={() => {
          if (!disabled) {
            onClick?.(tag as TTag)
          }
        }}
      >
        {!!tag.label && <TagContent tag={tag} />}
      </ToggleChip>
    )
  }

  return (
    <div
      onClick={() => {
        if (!disabled) {
          onClick?.(tag as TTag)
        }
      }}
      style={{
        backgroundColor: `${color(tagColor).fade(0.92)}`,
        border: `1px solid ${color(tagColor).fade(0.76)}`,
        color: `${color(tagColor).darken(0.1)}`,
      }}
      className={cx('chip', className)}
    >
      <TagContent tag={tag} />
    </div>
  )
}

export default Tag
