import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Tag from './Tag'
import { useGetTagsQuery } from 'common/services/useTag'

type TagValuesType = {
  onAdd?: () => void
  value?: number[]
  projectId: string

  hideNames?: boolean
}

const TagValues: FC<TagValuesType> = ({
  hideNames = true,
  onAdd,
  projectId,
  value,
}) => {
  const { data: tags } = useGetTagsQuery({ projectId })
  return (
    <Row className='tag-values'>
      {tags?.map(
        (tag) =>
          value?.includes(tag.id) && (
            <Tag
              hideNames={hideNames}
              onClick={onAdd}
              className='px-2 py-2 mr-2'
              tag={tag}
            />
          ),
      )}
      {!!onAdd && (
        <Button size='xSmall' onClick={onAdd} type='button' theme='outline'>
          Add Tag
        </Button>
      )}
    </Row>
  )
}

export default TagValues
