import React, { FC, useEffect, useState } from 'react'
import { find } from 'lodash'
import _data from 'common/data/base/_data'
import {
  AvailablePermission,
  GroupPermission,
  User,
  UserGroup,
  UserPermission,
} from 'common/types/responses'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import Format from 'common/utils/format'
import PanelSearch from './PanelSearch'
import Button from './base/forms/Button'
import InfoMessage from './InfoMessage'
import Switch from './Switch'
import TabItem from './base/forms/TabItem'
import Tabs from './base/forms/Tabs'
import UserGroupList from './UserGroupList'
import { PermissionLevel } from 'common/types/requests'
import { RouterChildContext } from 'react-router'
import { useGetAvailablePermissionsQuery } from 'common/services/useAvailablePermissions'
import ConfigProvider from 'common/providers/ConfigProvider'
import ModalHR from './modals/ModalHR'
import Icon from './Icon'
import {
  useCreateRoleEnvironmentPermissionMutation,
  useCreateRoleOrganisationPermissionMutation,
  useCreateRoleProjectPermissionMutation,
  useGetRoleEnvironmentPermissionsQuery,
  useGetRoleOrganisationPermissionsQuery,
  useGetRoleProjectPermissionsQuery,
  useUpdateRoleEnvironmentPermissionMutation,
  useUpdateRoleOrganisationPermissionMutation,
  useUpdateRoleProjectPermissionMutation,
} from 'common/services/useRolePermission'

const OrganisationProvider = require('common/providers/OrganisationProvider')
const Project = require('common/project')

type EditPermissionModalType = {
  group?: UserGroup
  id: string
  isGroup?: boolean
  level: PermissionLevel
  name: string
  onSave: () => void
  parentId?: string
  parentLevel?: string
  parentSettingsLink?: string
  permissions?: UserPermission[]
  push: (route: string) => void
  user?: User
  role?: Role
  // hasPermissions: () => void
}

type EditPermissionsType = Omit<EditPermissionModalType, 'onSave'> & {
  onSaveGroup?: () => void
  onSaveUser: () => void
  router: RouterChildContext['router']
  tabClassName?: string
}
type EntityPermissions = Omit<
  UserPermission,
  'user' | 'id' | 'group' | 'isGroup'
> & {
  id?: number
  user?: number
}

const _EditPermissionsModal: FC<EditPermissionModalType> = (props) => {
  const [entityPermissions, setEntityPermissions] = useState<EntityPermissions>(
    { admin: false, permissions: [] },
  )
  const [parentError, setParentError] = useState(false)
  const [saving, setSaving] = useState(false)
  const {
    group,
    id,
    isGroup,
    level,
    name,
    onSave,
    parentId,
    parentLevel,
    parentSettingsLink,
    push,
    role,
    user,
  } = props

  const { data: permissions } = useGetAvailablePermissionsQuery({ level })
  const processResults = (results: (UserPermission & GroupPermission)[]) => {
    let entityPermissions:
      | (Omit<EntityPermissions, 'user' | 'group' | 'role'> & {
          user?: any
          group?: any
          role?: any
        })
      | undefined = isGroup
      ? find(results || [], (r) => r.group.id === group?.id)
      : role
      ? find(results || [], (r) => r.role === role?.id)
      : find(results || [], (r) => r.user?.id === user?.id)

    if (!entityPermissions) {
      entityPermissions = { admin: false, permissions: [] }
    }
    if (user) {
      entityPermissions.user = user.id
    }
    if (group) {
      entityPermissions.group = group.id
    }
    return entityPermissions
  }

  const [
    updateRoleEnvironmentPermission,
    {
      isError: envUpdatedError,
      isLoading: isEnvPermUpdating,
      isSuccess: isEnvPermUpdated,
    },
  ] = useUpdateRoleEnvironmentPermissionMutation()
  const [
    updateRoleOrganisationPermission,
    {
      isError: orgUpdatedError,
      isLoading: isOrgPermUpdating,
      isSuccess: isOrgPermUpdated,
    },
  ] = useUpdateRoleOrganisationPermissionMutation()
  const [
    updateRoleProjectPermission,
    {
      isError: projectUpdatedError,
      isLoading: isProjectPermUpdating,
      isSuccess: isProjectPermUpdated,
    },
  ] = useUpdateRoleProjectPermissionMutation()
  const [
    createRoleEnvironmentPermission,
    {
      isError: envCreatedError,
      isLoading: isEnvPermCreating,
      isSuccess: isEnvPermCreated,
    },
  ] = useCreateRoleEnvironmentPermissionMutation()
  const [
    createRoleProjectPermission,
    {
      isError: orgCreatedError,
      isLoading: isProjectPermCreating,
      isSuccess: isProjectPermCreated,
    },
  ] = useCreateRoleProjectPermissionMutation()
  const [
    createRoleOrganisationPermission,
    {
      isError: projectCreatedError,
      isLoading: isOrgPermCreating,
      isSuccess: isOrgPermCreated,
    },
  ] = useCreateRoleOrganisationPermissionMutation()

  useEffect(() => {
    if (isEnvPermUpdating || isEnvPermCreating) {
      setSaving(true)
    }
    if (isEnvPermUpdated || isEnvPermCreated) {
      refetchEnvPerm()
      toast('Environment permissions Saved')
      setSaving(false)
    }
    if (envUpdatedError || envCreatedError) {
      toast('Failed to Save')
      setSaving(false)
    }
  }, [
    isEnvPermUpdating,
    isEnvPermCreating,
    isEnvPermUpdated,
    isEnvPermCreated,
    envUpdatedError,
    envCreatedError,
  ])

  useEffect(() => {
    if (isOrgPermUpdating || isOrgPermCreating) {
      setSaving(true)
    }
    if (isOrgPermUpdated || isOrgPermCreated) {
      refetchOrgPerm()
      toast('Organisation permissions Saved')
      setSaving(false)
    }
    if (orgUpdatedError || orgCreatedError) {
      toast('Failed to Save')
      setSaving(false)
    }
  }, [
    isOrgPermUpdating,
    isOrgPermCreating,
    isOrgPermUpdated,
    isOrgPermCreated,
    orgUpdatedError,
    orgCreatedError,
  ])

  useEffect(() => {
    if (isProjectPermUpdating || isProjectPermCreating) {
      setSaving(true)
    }
    if (isProjectPermUpdated || isProjectPermCreated) {
      refetchProjectPerm()
      toast('Project permissions Saved')
      setSaving(false)
    }
    if (projectUpdatedError || projectCreatedError) {
      toast('Failed to Save')
      setSaving(false)
    }
  }, [
    isProjectPermUpdating,
    isProjectPermCreating,
    isProjectPermUpdated,
    isProjectPermCreated,
    projectUpdatedError,
    projectCreatedError
  ])

  const {
    data,
    isLoading,
    refetch: refetchOrgPerm,
  } = useGetRoleOrganisationPermissionsQuery(
    {
      organisation_id: role?.organisation,
      role_id: role?.id,
    },
    { skip: !role },
  )

  const {
    data: projectPermissions,
    isLoading: projectIsLoading,
    refetch: refetchProjectPerm,
  } = useGetRoleProjectPermissionsQuery(
    {
      organisation_id: role?.organisation,
      project_id: id,
      role_id: role?.id,
    },
    { skip: !role || !id },
  )

  const {
    data: envPermissions,
    isLoading: envIsLoading,
    refetch: refetchEnvPerm,
  } = useGetRoleEnvironmentPermissionsQuery(
    {
      env_id: id,
      organisation_id: role?.organisation,
      role_id: role?.id,
    },
    { skip: !role || !id },
  )

  useEffect(() => {
    if (!isLoading && data && level === 'organisation') {
      const entityPermissions = processResults(data.results)
      setEntityPermissions(entityPermissions)
    }
  }, [data, isLoading])

  useEffect(() => {
    if (!projectIsLoading && projectPermissions && level === 'project') {
      const entityPermissions = processResults(projectPermissions?.results)
      setEntityPermissions(entityPermissions)
    }
  }, [projectPermissions, projectIsLoading])

  useEffect(() => {
    if (!envIsLoading && envPermissions && level === 'environment') {
      const entityPermissions = processResults(envPermissions?.results)
      setEntityPermissions(entityPermissions)
    }
  }, [envPermissions, envIsLoading])

  useEffect(() => {
    let parentGet = Promise.resolve()
    if (!role && parentLevel) {
      const parentUrl = isGroup
        ? `${parentLevel}s/${parentId}/user-group-permissions/`
        : `${parentLevel}s/${parentId}/user-permissions/`
      parentGet = _data
        .get(`${Project.api}${parentUrl}`)
        .then((results: (UserPermission & GroupPermission)[]) => {
          const entityPermissions = processResults(results)
          if (
            !entityPermissions.admin &&
            !entityPermissions.permissions.find(
              (v) => v === `VIEW_${parentLevel.toUpperCase()}`,
            )
          ) {
            // e.g. trying to set an environment permission but don't have view_projec
            setParentError(true)
          } else {
            setParentError(false)
          }
        })
    }
    if (!role) {
      parentGet
        .then(() => {
          const url = isGroup
            ? `${level}s/${id}/user-group-permissions/`
            : `${level}s/${id}/user-permissions/`
          _data
            .get(`${Project.api}${url}`)
            .then((results: (UserPermission & GroupPermission)[]) => {
              // @ts-ignore
              const entityPermissions = processResults(results)
              setEntityPermissions(entityPermissions)
            })
        })
        .catch(() => {
          setParentError(true)
        })
    }
    //eslint-disable-next-line
  }, [])

  const admin = () => entityPermissions && entityPermissions.admin

  const hasPermission = (key: string) => {
    if (admin()) return true
    return entityPermissions.permissions.includes(key)
  }

  const close = () => {
    closeModal()
  }

  const save = () => {
    const entityId =
      typeof entityPermissions.id === 'undefined' ? '' : entityPermissions.id
    if (!role) {
      const url = isGroup
        ? `${level}s/${id}/user-group-permissions/${entityId}`
        : `${level}s/${id}/user-permissions/${entityId}`
      setSaving(true)
      const action = entityId ? 'put' : 'post'
      _data[action](`${Project.api}${url}${entityId && '/'}`, entityPermissions)
        .then(() => {
          onSave && onSave()
          close()
        })
        .catch(() => {
          setSaving(false)
        })
    } else {
      if (entityId) {
        switch (level) {
          case 'organisation':
            updateRoleOrganisationPermission({
              body: {
                permissions: entityPermissions.permissions,
              },
              id: entityId,
              organisation_id: role.organisation,
              role_id: role.id,
            })
            break
          case 'project':
            updateRoleProjectPermission({
              body: {
                admin: entityPermissions.admin,
                permissions: entityPermissions.permissions,
                project: id,
              },
              id: entityPermissions.id,
              organisation_id: role.organisation,
              role_id: role.id,
            })
            break
          case 'environment':
            updateRoleEnvironmentPermission({
              body: {
                admin: entityPermissions.admin,
                environment: id,
                permissions: entityPermissions.permissions,
              },
              id: entityPermissions.id,
              organisation_id: role.organisation,
              role_id: 89,
            })
            break
          default:
            break
        }
      } else {
        switch (level) {
          case 'organisation':
            createRoleOrganisationPermission({
              body: {
                permissions: entityPermissions.permissions,
              },
              organisation_id: role.organisation,
              role_id: role.id,
            })
            break
          case 'project':
            createRoleProjectPermission({
              body: {
                admin: entityPermissions.admin,
                permissions: entityPermissions.permissions,
                project: id,
              },
              organisation_id: role.organisation,
              role_id: role.id,
            })
            break
          case 'environment':
            createRoleEnvironmentPermission({
              body: {
                admin: entityPermissions.admin,
                environment: id,
                permissions: entityPermissions.permissions,
              },
              organisation_id: role.organisation,
              role_id: role.id,
            })
            break
          default:
            break
        }
      }
    }
  }

  const togglePermission = (key: string) => {
    if (role) {
      const updatedPermissions = [...entityPermissions.permissions]
      const index = updatedPermissions.indexOf(key)
      if (index === -1) {
        updatedPermissions.push(key)
      } else {
        updatedPermissions.splice(index, 1)
      }

      setEntityPermissions({
        ...entityPermissions,
        permissions: updatedPermissions,
      })
    } else {
      const newEntityPermissions = { ...entityPermissions }

      const index = newEntityPermissions.permissions.indexOf(key)

      if (index === -1) {
        newEntityPermissions.permissions.push(key)
      } else {
        newEntityPermissions.permissions.splice(index, 1)
      }
      setEntityPermissions(newEntityPermissions)
    }
  }

  const toggleAdmin = () => {
    setEntityPermissions({
      ...entityPermissions,
      admin: !entityPermissions.admin,
    })
  }

  const isAdmin = admin()
  const hasRbacPermission = Utils.getPlansPermission('RBAC')

  return !permissions || !entityPermissions ? (
    <div className='modal-body text-center'>
      <Loader />
    </div>
  ) : (
    <div>
      <div className='modal-body'>
        <div className='mb-2'>
          {level !== 'organisation' && (
            <Row className={role ? 'px-3 py-2' : ''}>
              <Flex>
                <strong>Administrator</strong>
                <div className='list-item-footer faint'>
                  {hasRbacPermission ? (
                    `Full View and Write permissions for the given ${Format.camelCase(
                      level,
                    )}.`
                  ) : (
                    <span>
                      Role-based access is not available on our Free Plan.
                      Please visit{' '}
                      <a href='https://flagsmith.com/pricing/'>
                        our Pricing Page
                      </a>{' '}
                      for more information on our licensing options.
                    </span>
                  )}
                </div>
              </Flex>
              <Switch
                disabled={!hasRbacPermission}
                onChange={toggleAdmin}
                checked={isAdmin}
              />
            </Row>
          )}
        </div>
        <PanelSearch
          title='Permissions'
          className='no-pad mb-4'
          items={permissions}
          renderRow={(p: AvailablePermission) => {
            const levelUpperCase = level.toUpperCase()
            const disabled =
              level !== 'organisation' &&
              p.key !== `VIEW_${levelUpperCase}` &&
              !hasPermission(`VIEW_${levelUpperCase}`)
            return (
              <Row
                key={p.key}
                style={admin() ? { opacity: 0.5 } : undefined}
                className='list-item list-item-sm px-3'
              >
                <Row space>
                  <Flex>
                    <strong>{Format.enumeration.get(p.key)}</strong>
                    <div className='list-item-subtitle'>{p.description}</div>
                  </Flex>
                  <Switch
                    onChange={() => togglePermission(p.key)}
                    disabled={disabled || admin() || !hasRbacPermission}
                    checked={!disabled && hasPermission(p.key)}
                  />
                </Row>
              </Row>
            )
          }}
        />

        <p className='text-right mt-2'>
          This will edit the permissions for{' '}
          <strong>
            {isGroup
              ? `the ${name} group`
              : role
              ? ` ${role.name}`
              : ` ${name}`}
          </strong>
          .
        </p>

        {parentError && !role && (
          <InfoMessage>
            The selected {isGroup ? 'group' : 'user'} does not have explicit
            user permissions to view this {parentLevel}. If the user does not
            belong to any groups with this permissions, you may have to adjust
            their permissions in{' '}
            <a
              onClick={() => {
                if (parentSettingsLink) {
                  push(parentSettingsLink)
                }
                closeModal()
              }}
            >
              <strong>{parentLevel} settings</strong>
            </a>
            .
          </InfoMessage>
        )}
      </div>
      <ModalHR />

      <div className='modal-footer'>
        {!role && (
          <Button className='mr-2' onClick={closeModal} theme='secondary'>
            Cancel
          </Button>
        )}
        <Button
          onClick={save}
          data-test='update-feature-btn'
          id='update-feature-btn'
          disabled={saving || !hasRbacPermission}
        >
          {saving ? 'Saving' : 'Save'}
        </Button>
      </div>
    </div>
  )
}

export const EditPermissionsModal = ConfigProvider(_EditPermissionsModal)

const EditPermissions: FC<EditPermissionsType> = (props) => {
  const {
    id,
    level,
    onSaveGroup,
    onSaveUser,
    parentId,
    parentLevel,
    parentSettingsLink,
    permissions,
    router,
    tabClassName,
  } = props
  const [tab, setTab] = useState()
  const editUserPermissions = (user: User) => {
    openModal(
      `Edit ${Format.camelCase(level)} Permissions`,
      <EditPermissionsModal
        name={`${user.first_name} ${user.last_name}`}
        id={id}
        onSave={onSaveUser}
        level={level}
        parentId={parentId}
        parentLevel={parentLevel}
        parentSettingsLink={parentSettingsLink}
        user={user}
        push={router.history.push}
      />,
      'p-0',
    )
  }

  const editGroupPermissions = (group: UserGroup) => {
    openModal(
      `Edit ${Format.camelCase(level)} Permissions`,
      <EditPermissionsModal
        name={`${group.name}`}
        id={id}
        isGroup
        onSave={onSaveGroup}
        level={level}
        parentId={parentId}
        parentLevel={parentLevel}
        parentSettingsLink={parentSettingsLink}
        group={group}
        push={router.history.push}
      />,
      'p-0',
    )
  }

  return (
    <div className='mt-4'>
      <h5>Manage Users and Permissions</h5>
      <p className='fs-small lh-sm'>
        Flagsmith lets you manage fine-grained permissions for your projects and
        environments.{' '}
        <Button
          theme='text'
          href='https://docs.flagsmith.com/system-administration/rbac'
          target='_blank'
        >
          Learn about User Roles.
        </Button>
      </p>
      <Tabs value={tab} onChange={setTab} theme='pill'>
        <TabItem tabLabel='Users'>
          <OrganisationProvider>
            {({ isLoading, users }: { isLoading: boolean; users?: User[] }) => (
              <div className='mt-4'>
                {isLoading && !users?.length && (
                  <div className='centered-container'>
                    <Loader />
                  </div>
                )}
                {!!users?.length && (
                  <div>
                    <FormGroup className='panel no-pad pl-2 pr-2 panel--nested'>
                      <div className={tabClassName}>
                        <PanelSearch
                          id='org-members-list'
                          title='Users'
                          className='panel--transparent'
                          items={users}
                          itemHeight={64}
                          header={
                            <Row className='table-header'>
                              <Flex className='table-column px-3'>User</Flex>
                              <Flex className='table-column'>Role</Flex>
                              <div
                                style={{ width: '80px' }}
                                className='table-column text-center'
                              >
                                Action
                              </div>
                            </Row>
                          }
                          renderRow={({
                            email,
                            first_name,
                            id,
                            last_name,
                            role,
                          }: User) => {
                            const onClick = () => {
                              if (role !== 'ADMIN') {
                                editUserPermissions({
                                  email,
                                  first_name,
                                  id,
                                  last_name,
                                  role,
                                })
                              }
                            }
                            const matchingPermissions = permissions?.find(
                              (v) => v.user.id === id,
                            )

                            return (
                              <Row
                                onClick={onClick}
                                space
                                className={`list-item${
                                  role === 'ADMIN' ? '' : ' clickable'
                                }`}
                                key={id}
                              >
                                <Flex className='table-column px-3'>
                                  <div className='mb-1 font-weight-medium'>
                                    {`${first_name} ${last_name}`}{' '}
                                    {id == AccountStore.getUserId() && '(You)'}
                                  </div>
                                  <div className='list-item-subtitle'>
                                    {email}
                                  </div>
                                </Flex>
                                {role === 'ADMIN' ? (
                                  <Flex className='table-column fs-small lh-sm'>
                                    <Tooltip
                                      html
                                      title={'Organisation Administrator'}
                                    >
                                      {
                                        'Organisation administrators have all permissions enabled.<br/>To change the role of this user, visit Organisation Settings.'
                                      }
                                    </Tooltip>
                                  </Flex>
                                ) : (
                                  <Flex
                                    onClick={onClick}
                                    className='table-column fs-small lh-sm'
                                  >
                                    {matchingPermissions &&
                                    matchingPermissions.admin
                                      ? `${Format.camelCase(
                                          level,
                                        )} Administrator`
                                      : 'Regular User'}
                                  </Flex>
                                )}
                                <div
                                  style={{ width: '80px' }}
                                  className='text-center'
                                >
                                  {role !== 'ADMIN' && (
                                    <Icon
                                      name='setting'
                                      width={20}
                                      fill='#656D7B'
                                    />
                                  )}
                                </div>
                              </Row>
                            )
                          }}
                          renderNoResults={
                            <div>You have no users in this organisation.</div>
                          }
                          filterRow={(item: User, search: string) => {
                            const strToSearch = `${item.first_name} ${item.last_name} ${item.email}`
                            return (
                              strToSearch
                                .toLowerCase()
                                .indexOf(search.toLowerCase()) !== -1
                            )
                          }}
                        />
                      </div>

                      <div id='select-portal' />
                    </FormGroup>
                  </div>
                )}
              </div>
            )}
          </OrganisationProvider>
        </TabItem>
        <TabItem tabLabel='Groups'>
          <FormGroup className='panel no-pad pl-2 mt-4 pr-2 panel--nested'>
            <div className={tabClassName}>
              <UserGroupList
                noTitle
                orgId={AccountStore.getOrganisation().id}
                onClick={(group: UserGroup) => editGroupPermissions(group)}
              />
            </div>
          </FormGroup>
        </TabItem>
      </Tabs>
    </div>
  )
}

export default ConfigProvider(EditPermissions) as unknown as FC<
  Omit<EditPermissionsType, 'router'>
>
