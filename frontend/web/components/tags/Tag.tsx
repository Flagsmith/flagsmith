import React, { FC } from 'react'
import color from 'color'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import Format from 'common/utils/format'

type TagType = {
  className?: string
  deselectedColor?: string
  hideNames?: boolean
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
  isTruncated?: boolean
}

const Tag: FC<TagType> = ({
  className,
  deselectedColor,
  hideNames,
  isTruncated,
  onClick,
  selected,
  tag,
}) => {
  const getColor = () => {
    if (Utils.getFlagsmithHasFeature('dark_mode') && tag.color === '#344562') {
      return '#9DA4AE'
    }
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
    <Tooltip
      plainText
      title={
        <div
          onClick={() => onClick?.(tag as TTag)}
          style={{
            backgroundColor: `${color(getColor()).fade(0.92)}`,
            border: `1px solid ${color(getColor()).fade(0.76)}`,
            color: `${color(getColor()).darken(0.1)}`,
          }}
          className={cx('chip', className)}
        >
          {isTruncated ? Format.truncateText(`${tag.label}`, 1) : tag.label}
        </div>
      }
    >
      {tag.label}
    </Tooltip>
  )
}

export default Tag
