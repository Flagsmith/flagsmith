import React, { FC, Fragment, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Tag from './Tag'
import { useGetTagsQuery } from 'common/services/useTag'

type TagValuesType = {
  onAdd?: () => void
  value?: number[]
  projectId: string
  children?: ReactNode
  inline?: boolean
  hideNames?: boolean
}

const TagValues: FC<TagValuesType> = ({
  children,
  hideNames = true,
  inline,
  onAdd,
  projectId,
  value,
}) => {
  const { data: tags } = useGetTagsQuery({ projectId })
  const Wrapper = inline ? Fragment : Row
  return (
    <Wrapper className='tag-values align-content-center'>
      {children}
      {tags?.map(
        (tag) =>
          value?.includes(tag.id) && (
            <Tag
              className='chip--xs'
              hideNames={hideNames}
              onClick={onAdd}
              tag={tag}
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
