import React, { FC, Fragment, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Tag from './Tag'
import { useGetTagsQuery } from 'common/services/useTag'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import { Tag as TTag } from 'common/types/responses'
import { ProjectPermission } from 'common/types/permissions.types'

type TagValuesType = {
  onAdd?: (tag?: TTag) => void
  /** Optional callback function to handle click events on tags. If provided, it will override the onAdd callback. */
  onClick?: (tag?: TTag) => void
  value?: number[]
  projectId: string
  children?: ReactNode
  inline?: boolean
  hideTags?: number[]
}

const TagValues: FC<TagValuesType> = ({
  children,
  hideTags = [],
  inline,
  onAdd,
  onClick,
  projectId,
  value,
}) => {
  const { data } = useGetTagsQuery({ projectId })
  const Wrapper = inline ? Fragment : Row

  // Filtered here, not in Tag: a chip has no business reading feature flags.
  const isFeatureHealthEnabled = Utils.getFlagsmithHasFeature('feature_health')

  const tags = data?.filter(
    (tag) =>
      !hideTags?.includes(tag.id) &&
      (isFeatureHealthEnabled || tag.type !== 'UNHEALTHY'),
  )

  const { permission: createEditTagPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.MANAGE_TAGS,
  })

  return (
    <Wrapper className='row-gap-2 align-content-center'>
      {children}
      {tags?.map(
        (tag) =>
          value?.includes(tag.id) && (
            <Tag
              disabled={Utils.tagDisabled(tag)}
              key={tag.id}
              // The chip hands back a Partial; callers here want the whole tag.
              onClick={() => (onAdd ?? onClick)?.(tag)}
              tag={tag}
            />
          ),
      )}
      {!!onAdd &&
        Utils.renderWithPermission(
          createEditTagPermission,
          Constants.projectPermissions(ProjectPermission.MANAGE_TAGS),
          <Button
            disabled={!createEditTagPermission}
            size='xxSmall'
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
