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

  // Feature health is a paid feature, and its tag is applied by the system
  // rather than chosen, so with the feature off the tag should not appear at
  // all. Filtered here rather than inside Tag, which has no business knowing
  // about feature flags: this is the display path for ProjectFeatureRow,
  // FeatureOverrideRow, FeatureTags, ReleaseManagerPage and
  // FlagEnvironmentsPage.
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
    <Wrapper className='tag-values align-content-center'>
      {children}
      {tags?.map(
        (tag) =>
          value?.includes(tag.id) && (
            <Tag
              disabled={Utils.tagDisabled(tag)}
              key={tag.id}
              // Closes over the real tag from the query rather than taking the
              // Partial the chip hands back, so callers still get a whole one.
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
