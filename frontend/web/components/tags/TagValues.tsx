import React, { FC, Fragment, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Tag from './Tag'
import { useGetTagsQuery } from 'common/services/useTag'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'

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
  const permissionType = Utils.getFlagsmithHasFeature('manage_tags_permission')
    ? 'MANAGE_TAGS'
    : 'ADMIN'

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
              className='chip--xs'
              hideNames={hideNames}
              onClick={onAdd}
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
            onClick={onAdd}
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
