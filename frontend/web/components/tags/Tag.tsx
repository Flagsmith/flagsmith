import React, { FC } from 'react'
import color from 'color'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import ToggleChip from 'components/ToggleChip'

type TagType = {
  className?: string
  deselectedColor?: string
  hideNames?: boolean
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
}

const Tag: FC<TagType> = ({
  className,
  deselectedColor,
  hideNames,
  onClick,
  selected,
  tag,
}) => {
  const getColor = () => {
    if (selected) {
      return tag.color
    }
    return deselectedColor || tag.color
  }

  if (!hideNames) {
    return (
      <ToggleChip
        color={getColor()}
        active={selected}
        onClick={onClick ? () => onClick(tag as TTag) : null}
      >
        {tag.label}
      </ToggleChip>
    )
  }

  return (
    <div
      onClick={() => onClick?.(tag as TTag)}
      style={{
        backgroundColor: `${color(getColor()).fade(0.92)}`,
        border: `1px solid ${color(getColor()).fade(0.76)}`,
        color: `${color(getColor()).darken(0.1)}`,
      }}
      className={cx('chip', 'chip--sm', className)}
    >
      {tag.label}
    </div>
  )
}

export default Tag
