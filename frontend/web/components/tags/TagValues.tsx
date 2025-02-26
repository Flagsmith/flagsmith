import React, { FC, Fragment, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Tag from './Tag'
import { useGetTagsQuery } from 'common/services/useTag'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import { Tag as TTag } from 'common/types/responses'

type TagValuesType = {
  onAdd?: (tag?: TTag) => void
  /** Optional callback function to handle click events on tags. If provided, it will override the onAdd callback. */
  onClick?: (tag?: TTag) => void
  value?: number[]
  projectId: string
  children?: ReactNode
  inline?: boolean
  hideNames?: boolean
  hideTags?: number[]
}

const TagValues: FC<TagValuesType> = ({
  children,
  hideNames = true,
  hideTags = [],
  inline,
  onAdd,
  onClick,
  projectId,
  value,
}) => {
  const { data } = useGetTagsQuery({ projectId })
  const Wrapper = inline ? Fragment : Row
  const permissionType = 'MANAGE_TAGS'

  const tags = data?.filter((tag) => !hideTags?.includes(tag.id))

  const { permission: createEditTagPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: permissionType,
  })

  return (
    <Wrapper className='tag-values align-content-center'>
      {children}
      {tags?.map(
        (tag) =>
          value?.includes(tag.id) && (
            <Tag
              key={tag.id}
              className='chip--xs'
              hideNames={hideNames}
              onClick={onAdd ?? onClick}
              tag={tag}
            />
          ),
      )}
      {!!onAdd &&
        Utils.renderWithPermission(
          createEditTagPermission,
          Constants.projectPermissions(
            permissionType === 'ADMIN' ? 'Admin' : 'Manage Tags',
          ),
          <Button
            disabled={!createEditTagPermission}
            size='xSmall'
            onClick={() => onAdd?.()}
            type='button'
            theme='outline'
          >
            Add Tag
          </Button>,
        )}
    </Wrapper>
  )
}

export default TagValues
