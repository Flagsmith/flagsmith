import React, { useState, forwardRef, useImperativeHandle } from 'react'
import Icon from 'components/Icon'
import { EditPermissionsModal } from 'components/EditPermissions'
import {
  useGetRoleProjectPermissionsQuery,
  useGetRoleEnvironmentPermissionsQuery,
} from 'common/services/useRolePermission'
import Format from 'common/utils/format'

type MainItem = {
  name: string
  id: string
}

type CollapsibleNestedListProps = {
  mainItems: MainItem[]
  role: Role
  level: string
}

const CollapsibleNestedList: React.FC<CollapsibleNestedListProps> = forwardRef(
  ({ level, mainItems, role }, ref) => {
    const [expandedItems, setExpandedItems] = useState<string[]>([])
    const [unsavedProjects, setUnsavedProjects] = useState<string[]>([])

    const toggleExpand = (id: string) => {
      setExpandedItems((prevExpanded) =>
        prevExpanded.includes(id)
          ? prevExpanded.filter((item) => item !== id)
          : [...prevExpanded, id],
      )
    }

    const removeUnsavedProject = (projectId) => {
      setUnsavedProjects((prevUnsavedProjects) =>
        prevUnsavedProjects.filter((id) => id !== projectId),
      )
    }

    useImperativeHandle(
      ref,
      () => {
        return {
          onClosing() {
            if (unsavedProjects.length > 0) {
              return new Promise((resolve) => {
                openConfirm(
                  'Are you sure?',
                  'Closing this will discard your unsaved changes.',
                  () => resolve(true),
                  () => resolve(false),
                  'Ok',
                  'Cancel',
                )
              })
            } else {
              return Promise.resolve(true)
            }
          },
          tabChanged() {
            return unsavedProjects.length > 0
          },
        }
      },
      [unsavedProjects],
    )

    const PermissionsSummary = ({ levelId }) => {
      const { data: projectPermissions, isLoading: projectIsLoading } =
        useGetRoleProjectPermissionsQuery(
          {
            organisation_id: role?.organisation,
            project_id: levelId,
            role_id: role?.id,
          },
          { skip: !levelId || level !== 'project' },
        )

      const { data: envPermissions, isLoading: envIsLoading } =
        useGetRoleEnvironmentPermissionsQuery(
          {
            env_id: levelId,
            organisation_id: role?.organisation,
            role_id: role?.id,
          },
          { skip: !levelId || level !== 'environment' },
        )

      const permissions = projectPermissions || envPermissions
      const roleResult = permissions?.results.filter(
        (item) => item.role === role?.id,
      )
      const roleRermissions =
        roleResult && roleResult.length > 0 ? roleResult[0].permissions : []

      const isAdmin =
        roleResult && roleResult.length > 0 ? roleResult[0].admin : false

      const permissionsSummary =
        (roleRermissions &&
          roleRermissions.length > 0 &&
          roleRermissions
            .map((item) => Format.enumeration.get(item))
            .join(', ')) ||
        ''

      return projectIsLoading || envIsLoading ? (
        <div className='modal-body text-center'>
          <Loader />
        </div>
      ) : (
        <div>{isAdmin ? 'Administrator' : permissionsSummary}</div>
      )
    }

    return (
      <div
        style={{
          borderRadius: '10px',
          minHeight: '60px',
        }}
      >
        {mainItems.map((mainItem, index) => (
          <div key={index}>
            <Row
              key={index}
              onClick={() => toggleExpand(mainItem.id)}
              style={{
                backgroundColor: '#fafafb',
                border: '1px solid rgba(101, 109, 123, 0.16)',
                borderRadius: '10px',
                opacity: 1,
              }}
              className='clickable cursor-pointer list-item-sm px-3'
            >
              <Flex>
                <div className={'list-item-subtitle'}>
                  <strong>{mainItem.name}</strong>{' '}
                  {unsavedProjects.includes(mainItem.id) && (
                    <div className='unread'>Unsaved</div>
                  )}
                </div>
              </Flex>
              <Flex>
                <div className={'list-item-subtitle'}>
                  <PermissionsSummary levelId={mainItem.id} />
                </div>
              </Flex>
              <Icon
                name={
                  expandedItems.includes(mainItem.id)
                    ? 'chevron-down'
                    : 'chevron-right'
                }
                width={25}
              />
            </Row>
            <div>
              {expandedItems.includes(mainItem.id) && (
                <EditPermissionsModal
                  id={mainItem.id}
                  level={level}
                  role={role}
                  permissionChanged={() => {
                    if (!unsavedProjects.includes(mainItem.id)) {
                      setUnsavedProjects((prevUnsavedProjects) => [
                        ...prevUnsavedProjects,
                        mainItem.id,
                      ])
                    }
                  }}
                  onSave={() => removeUnsavedProject(mainItem.id)}
                />
              )}
            </div>
          </div>
        ))}
      </div>
    )
  },
)

export default CollapsibleNestedList
