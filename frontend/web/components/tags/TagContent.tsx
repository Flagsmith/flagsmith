import React, { FC } from 'react'
import { Tag as TTag } from 'common/types/responses'
import Icon from 'components/Icon'
import color from 'color'
import Format from 'common/utils/format'

type TagContent = {
  tag: Partial<TTag>
  truncateTo?: Number
}

const TagContent: FC<TagContent> = ({ tag, truncateTo }) => {
  let tagLabel = tag.label
  if (truncateTo) {
    tagLabel = Format.truncateText(tagLabel, truncateTo)
  }

  if (tag.is_system_tag) {
    return (
      <span className={'mr-1'}>
        <Icon
          name={'moon'} // TODO: replace with better icon!
          fill={color(tag.color).darken(0.1).string()}
        ></Icon>{' '}
        {tagLabel}
      </span>
    )
  }

  if (tag.is_permanent) {
    return (
      <span className={'mr-1'}>
        <Icon
          name={'sun'} // TODO: replace with better icon!
          fill={color(tag.color).darken(0.1).string()}
        ></Icon>{' '}
        {tagLabel}
      </span>
    )
  }

  return <span>{tagLabel}</span>
}

export default TagContent
