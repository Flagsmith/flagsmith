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
  const [tagBasedPermissionsEnabled, setTagBasedPermissionsEnabled] =
    useState<boolean>(!!role?.tags?.length)
  const matchingTags = useMemo(() => {
    if (!role?.tags || !tags?.length) return []
    return role.tags.filter((id) => tags?.find((tag) => tag.id === id))
  }, [tags, role?.tags])
  if (!showTagBasedPermissions) return null
  return (
    <>
      {!!showTagBasedPermissions && !!role && (
        <div className='mt-4 mb-2'>
          <div className='d-flex align-items-center gap-2 fw-semibold'>
            <Switch
              disabled={!!matchingTags?.length || roleUpdating}
              checked={tagBasedPermissionsEnabled}
              onChange={(v: boolean) => {
                if (!v) {
                  setTagBasedPermissionsEnabled(false)
                  updateRole({
                    body: {
                      ...role,
                      tags: role.tags.filter((v) => !matchingTags.includes(v)),
                    },
                    organisation_id: role.organisation,
                    role_id: role.id,
                  })
                } else {
                  setTagBasedPermissionsEnabled(true)
                }
              }}
            />
            <Tooltip
              tooltipClassName='fw-normal'
              title={'Restrict permissions to tagged features'}
            >
              {`This will restrict <strong>Delete Feature</strong>,
        <strong>Update Feature State</strong>,
        <strong>Segment Overrides</strong> and <strong>Change Requests</strong>
        to only features with the assigned tags.
        <br /> <br />
        <strong>
          This will apply across all environments within the project where the
          environment admin permission is not enabled.
        </strong>`}
            </Tooltip>
            <a
              target='_blank'
              href='https://docs.flagsmith.com/system-administration/rbac#tags'
              className='fw-normal text-primary'
              rel='noreferrer'
            >
              View Docs
            </a>
          </div>
        </div>
      )}
      {tagBasedPermissionsEnabled && role && projectId && (
        <div className='mb-2'>
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
