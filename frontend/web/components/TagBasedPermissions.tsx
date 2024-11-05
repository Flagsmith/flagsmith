import React, { FC, useMemo, useState } from 'react'
import InfoMessage from './InfoMessage'
import { useUpdateRoleMutation } from 'common/services/useRole'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import { Role } from 'common/types/responses'
import Switch from './Switch'
import AddEditTags from './tags/AddEditTags'
import Tooltip from './Tooltip'

type TaggedPermissionsType = {
  role: Role | undefined
  projectId: string
}

const TagBasedPermissions: FC<TaggedPermissionsType> = ({
  projectId,
  role,
}) => {
  const [updateRole, { isLoading: roleUpdating }] = useUpdateRoleMutation({})
  const tag_based_permissions = Utils.getFlagsmithHasFeature(
    'tag_based_permissions',
  )
  const { data: tags } = useGetTagsQuery(
    { projectId: `${projectId}` },
    { skip: !projectId || !role },
  )
  const showTagBasedPermissions = projectId && tag_based_permissions && !!role
  const matchingTags = useMemo(() => {
    if (!role?.tags || !tags?.length) return []
    return role.tags.filter((id) => tags?.find((tag) => tag.id === id))
  }, [tags, role?.tags])
  if (!showTagBasedPermissions) return null
  return (
    <>
      {role?.tag_based && (
        <div className='mb-2'>
          <div className='mt-2 text-body fw-bold'>
            Enable permissions for the following tags:
          </div>
          <AddEditTags
            projectId={projectId}
            value={matchingTags}
            onChange={(newTags) => {
              updateRole({
                body: {
                  ...role,
                  tags: role.tags
                    .filter((v) => !matchingTags.includes(v))
                    .concat(newTags),
                },
                organisation_id: role.organisation,
                role_id: role.id,
              })
            }}
          />
        </div>
      )}
    </>
  )
}

export default TagBasedPermissions
