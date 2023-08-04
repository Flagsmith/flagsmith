import React, { FC, Fragment } from 'react'
import Button from 'components/base/forms/Button'
import Tag from './Tag'
import { useGetTagsQuery } from 'common/services/useTag'

type TagValuesType = {
  onAdd?: () => void
  value?: number[]
  projectId: string

  inline?: boolean
  hideNames?: boolean
}

const TagValues: FC<TagValuesType> = ({
  hideNames = true,
  inline,
  onAdd,
  projectId,
  value,
}) => {
  const { data: tags } = useGetTagsQuery({ projectId })
  const Wrapper = inline ? Fragment : Row
  return (
    <Wrapper className='tag-values'>
      {tags?.map(
        (tag) =>
          value?.includes(tag.id) && (
            <Tag
              className='chip--xs'
              hideNames={hideNames}
              onClick={onAdd}
              tag={tag}
              isTruncated={tag.label.length > 12}
            />
          ),
      )}
      {!!onAdd && (
        <Button size='xSmall' onClick={onAdd} type='button' theme='outline'>
          Add Tag
        </Button>
      )}
    </Wrapper>
  )
}

export default TagValues
