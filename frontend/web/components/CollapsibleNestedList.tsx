import React, { useState } from 'react'
import Icon from 'components/Icon'
import { EditPermissionsModal } from 'components/EditPermissions'
import {
  useGetRoleProjectPermissionsQuery,
  useGetRoleEnvironmentPermissionsQuery,
} from 'common/services/useRolePermission'
import Format from 'common/utils/format'

type MainItem = {
  name: string
}

type CollapsibleNestedListProps = {
  mainItems: MainItem[]
  isButtonVisible: boolean
  role: Role
  level: string
}

const CollapsibleNestedList: React.FC<CollapsibleNestedListProps> = ({
  level,
  mainItems,
  role,
}) => {
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpand = (id: string) => {
    setExpandedItems((prevExpanded) =>
      prevExpanded.includes(id)
        ? prevExpanded.filter((item) => item !== id)
        : [...prevExpanded, id],
    )
  }

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
    const isAdmin = permissions?.results[0]?.admin || false
    const permissionsSummary =
      permissions?.results[0]?.permissions
        .map((item) => Format.enumeration.get(item))
        .join(', ') || ''

    return projectIsLoading || envIsLoading ? (
      <div className='modal-body text-center'>
        <Loader />
      </div>
    ) : (
      <div>
        <strong>{isAdmin ? 'Administrator' : permissionsSummary}</strong>
      </div>
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
              <div className={'list-item-subtitle'}>{mainItem.name}</div>
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
              />
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default CollapsibleNestedList
