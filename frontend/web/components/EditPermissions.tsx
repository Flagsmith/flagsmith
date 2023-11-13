import React, {
  FC,
  useEffect,
  useState,
  forwardRef,
  useImperativeHandle,
} from 'react'
import { find } from 'lodash'
import { close as closeIcon } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

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
import Icon from './Icon'
import {
  useGetRoleEnvironmentPermissionsQuery,
  useGetRoleOrganisationPermissionsQuery,
  useGetRoleProjectPermissionsQuery,
  useCreateRolePermissionsMutation,
  useUpdateRolePermissionsMutation,
} from 'common/services/useRolePermission'

import {
  useCreateRolesPermissionUsersMutation,
  useDeleteRolesPermissionUsersMutation,
} from 'common/services/useRolesUser'

import {
  useCreateRolePermissionGroupMutation,
  useDeleteRolePermissionGroupMutation,
} from 'common/services/useRolePermissionGroup'

import MyRoleSelect from './MyRoleSelect'
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
  permissionChanged: () => void
  editPermissionsFromSettings?: boolean
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

const _EditPermissionsModal: FC<EditPermissionModalType> = forwardRef(
  (props, ref) => {
    const [entityPermissions, setEntityPermissions] =
      useState<EntityPermissions>({ admin: false, permissions: [] })
    const [parentError, setParentError] = useState(false)
    const [saving, setSaving] = useState(false)
    const [showRoles, setShowRoles] = useState<boolean>(false)
    const [rolesSelected, setRolesSelected] = useState<Array>([])
    const {
      editPermissionsFromSettings,
      envId,
      group,
      id,
      isGroup,
      level,
      name,
      onSave,
      parentId,
      parentLevel,
      parentSettingsLink,
      permissionChanged,
      push,
      role,
      roles,
      user,
    } = props
    useImperativeHandle(
      ref,
      () => {
        return {
          onClosing() {
            if (valueChanged) {
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
        }
      },
      [],
    )
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
      createRolePermissionUser,
      { data: usersData, isSuccess: userAdded },
    ] = useCreateRolesPermissionUsersMutation()

    const [deleteRolePermissionUser] = useDeleteRolesPermissionUsersMutation()

    const [
      createRolePermissionGroup,
      { data: groupsData, isSuccess: groupAdded },
    ] = useCreateRolePermissionGroupMutation()

    const [deleteRolePermissionGroup] = useDeleteRolePermissionGroupMutation()

    const [
      updateRolePermissions,
      {
        isError: errorUpdating,
        isLoading: isRolePermUpdating,
        isSuccess: isRolePermUpdated,
      },
    ] = useUpdateRolePermissionsMutation()

    const [
      createRolePermissions,
      {
        isError: errorCreating,
        isLoading: isRolePermCreating,
        isSuccess: isRolePermCreated,
      },
    ] = useCreateRolePermissionsMutation()

    useEffect(() => {
      const isSaving = isRolePermCreating || isRolePermUpdating
      if (isSaving) {
        setSaving(true)
      }
      if (isRolePermCreated || isRolePermUpdated) {
        toast(
          `${level.charAt(0).toUpperCase() + level.slice(1)} permissions Saved`,
        )
        permissionChanged?.()
        onSave?.()
        setSaving(false)
        if (editPermissionsFromSettings) {
          close()
        }
      }
      if (errorUpdating || errorCreating) {
        setSaving(false)
      }
    }, [
      errorUpdating,
      errorCreating,
      isRolePermCreated,
      isRolePermUpdated,
      isRolePermCreating,
      isRolePermUpdating,
    ])

    const { data: organisationPermissions, isLoading: organisationIsLoading } =
      useGetRoleOrganisationPermissionsQuery(
        {
          organisation_id: role?.organisation,
          role_id: role?.id,
        },
        { skip: !role },
      )

    const { data: projectPermissions, isLoading: projectIsLoading } =
      useGetRoleProjectPermissionsQuery(
        {
          organisation_id: role?.organisation,
          project_id: id,
          role_id: role?.id,
        },
        {
          skip:
            !id ||
            envId ||
            !Utils.getFlagsmithHasFeature('show_role_management'),
        },
      )

    const { data: envPermissions, isLoading: envIsLoading } =
      useGetRoleEnvironmentPermissionsQuery(
        {
          env_id: envId || id,
          organisation_id: role?.organisation,
          role_id: role?.id,
        },
        {
          skip:
            !role ||
            !id ||
            !Utils.getFlagsmithHasFeature('show_role_management'),
        },
      )
    useEffect(() => {
      if (
        !organisationIsLoading &&
        organisationPermissions &&
        level === 'organisation'
      ) {
        const entityPermissions = processResults(
          organisationPermissions.results,
        )
        setEntityPermissions(entityPermissions)
      }
    }, [organisationPermissions, organisationIsLoading])

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
        _data[action](
          `${Project.api}${url}${entityId && '/'}`,
          entityPermissions,
        )
          .then(() => {
            onSave && onSave()
            close()
          })
          .catch(() => {
            setSaving(false)
          })
      } else {
        const body = {
          permissions: entityPermissions.permissions,
        }
        if (level === 'project') {
          body.admin = entityPermissions.admin
          body.project = id
        }
        if (level === 'environment') {
          body.admin = entityPermissions.admin
          body.environment = envId || id
        }
        if (entityId) {
          updateRolePermissions({
            body,
            id: entityId,
            level: level === 'organisation' ? level : `${level}s`,
            organisation_id: role.organisation,
            role_id: role.id,
          })
        } else {
          createRolePermissions({
            body,
            id: entityId,
            level: level === 'organisation' ? level : `${level}s`,
            organisation_id: role.organisation,
            role_id: role.id,
          })
        }
      }
    }

    const togglePermission = (key: string) => {
      if (role) {
        permissionChanged?.()
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
      permissionChanged?.()
      setEntityPermissions({
        ...entityPermissions,
        admin: !entityPermissions.admin,
      })
    }
    const addRole = (roleId: string) => {
      if (level === 'organisation') {
        if (user) {
          createRolePermissionUser({
            data: {
              user: user.id,
            },
            organisation_id: id,
            role_id: roleId,
          })
        }
        if (group) {
          createRolePermissionGroup({
            data: {
              group: group.id,
            },
            organisation_id: id,
            role_id: roleId,
          })
        }
      }
    }

    const removeOwner = (roleId: string) => {
      const roleSelected = rolesAdded.find((item) => item.id === roleId)
      if (level === 'organisation') {
        if (user) {
          deleteRolePermissionUser({
            organisation_id: id,
            role_id: roleId,
            user_id: roleSelected.user_role_id,
          })
        }
        if (group) {
          deleteRolePermissionGroup({
            group_id: roleSelected.group_role_id,
            organisation_id: id,
            role_id: roleId,
          })
        }
      }
      setRolesSelected((rolesSelected || []).filter((v) => v.role !== roleId))
      toast('User role was removed')
    }

    useEffect(() => {
      if (userAdded || groupAdded) {
        if (user) {
          setRolesSelected(
            (rolesSelected || []).concat({
              role: usersData?.role,
              user_role_id: usersData?.id,
            }),
          )
        }
        if (group) {
          setRolesSelected(
            (rolesSelected || []).concat({
              group_role_id: groupsData?.id,
              role: groupsData?.role,
            }),
          )
        }
        toast('Role assigned')
      }
    }, [userAdded, usersData, groupsData, groupAdded])

    const getRoles = (roles = [], selectedRoles) => {
      return roles
        .filter((v) => selectedRoles.find((a) => a.role === v.id))
        .map((role) => {
          const matchedRole = selectedRoles.find((r) => r.role === role.id)
          if (matchedRole) {
            if (user) {
              return {
                ...role,
                user_role_id: matchedRole.user_role_id,
              }
            }
            if (group) {
              return {
                ...role,
                group_role_id: matchedRole.group_role_id,
              }
            }
          }
          return role
        })
    }

    const rolesAdded = getRoles(roles, rolesSelected || [])

    const isAdmin = admin()
    const hasRbacPermission = Utils.getPlansPermission('RBAC')

    return !permissions || !entityPermissions ? (
      <div className='modal-body text-center'>
        <Loader />
      </div>
    ) : (
      <div>
        <div className='modal-body px-4'>
          <div className='mb-2 mt-4'>
            {level !== 'organisation' && (
              <Row className={role ? 'px-3 py-2' : ''}>
                <Flex>
                  <div className='font-weight-medium text-dark mb-1'>
                    Administrator
                  </div>
                  <div className='list-item-footer faint'>
                    {hasRbacPermission ? (
                      `Full View and Write permissions for the given ${Format.camelCase(
                        level,
                      )}.`
                    ) : (
                      <span>
                        Role-based access is not available on our Free Plan.
                        Please visit{' '}
                        <a
                          href='https://flagsmith.com/pricing/'
                          className='text-primary'
                        >
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
            className='no-pad mb-2'
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

          <p className='text-right mt-5 text-dark'>
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
            <div className='mt-4'>
              <InfoMessage>
                The selected {isGroup ? 'group' : 'user'} does not have explicit
                user permissions to view this {parentLevel}. If the user does
                not belong to any groups with this permissions, you may have to
                adjust their permissions in{' '}
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
            </div>
          )}
        </div>
        {Utils.getFlagsmithHasFeature('show_role_management') &&
          roles &&
          level === 'organisation' && (
            <FormGroup className='px-4'>
              <InputGroup
                component={
                  <div>
                    <Row>
                      <strong style={{ width: 70 }}>Roles: </strong>
                      {rolesAdded?.map((r) => (
                        <Row
                          key={r.id}
                          onClick={() => removeOwner(r.id)}
                          className='chip'
                          style={{ marginBottom: 4, marginTop: 4 }}
                        >
                          <span className='font-weight-bold'>{r.name}</span>
                          <span className='chip-icon ion'>
                            <IonIcon
                              icon={closeIcon}
                              style={{ fontSize: '13px' }}
                            />
                          </span>
                        </Row>
                      ))}
                      <Button
                        theme='text'
                        onClick={() => setShowRoles(true)}
                        style={{ width: 70 }}
                      >
                        Add Role
                      </Button>
                    </Row>
                  </div>
                }
                type='text'
                title='Assign roles'
                tooltip='Assigns what role the user/group will have'
                inputProps={{
                  className: 'full-width',
                  style: { minHeight: 80 },
                }}
                className='full-width'
                placeholder='Add an optional description...'
              />
            </FormGroup>
          )}
        {Utils.getFlagsmithHasFeature('show_role_management') && (
          <div className='px-4'>
            <MyRoleSelect
              orgId={id}
              level={level}
              value={rolesSelected.map((v) => v.role)}
              onAdd={addRole}
              onRemove={removeOwner}
              isOpen={showRoles}
              onToggle={() => setShowRoles(!showRoles)}
            />
          </div>
        )}
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
            {saving ? 'Saving' : 'Save Permissions'}
          </Button>
        </div>
      </div>
    )
  },
)

export const EditPermissionsModal = ConfigProvider(_EditPermissionsModal)

const rolesWidths = [250, 600, 100]
const EditPermissions: FC<EditPermissionsType> = (props) => {
  const {
    envId,
    id,
    level,
    onSaveGroup,
    onSaveUser,
    parentId,
    parentLevel,
    parentSettingsLink,
    permissions,
    roleTabTitle,
    roles,
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
      'p-0 side-modal',
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
      'p-0 side-modal',
    )
  }
  const editRolePermissions = (role) => {
    openModal(
      `Edit ${Format.camelCase(level)} Role Permissions`,
      <EditPermissionsModal
        name={`${role.name}`}
        id={id}
        editPermissionsFromSettings
        envId={envId}
        level={level}
        role={role}
      />,
      'p-0 side-modal',
    )
  }
  const hasRbacPermission = Utils.getPlansPermission('RBAC')

  return (
    <div className='mt-4'>
      <h5>Manage Permissions</h5>
      <p className='fs-small lh-sm col-md-8 mb-4'>
        Flagsmith lets you manage fine-grained permissions for your projects and
        environments.{' '}
        <Button
          theme='text'
          href='https://docs.flagsmith.com/system-administration/rbac'
          target='_blank'
          className='fw-normal'
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
        {Utils.getFlagsmithHasFeature('show_role_management') && (
          <TabItem tabLabel='Roles'>
            {hasRbacPermission ? (
              <>
                <Row space className='mt-4'>
                  <h5 className='m-b-0'>{roleTabTitle}</h5>
                </Row>
                <PanelSearch
                  id='org-members-list'
                  title={'Roles'}
                  className='no-pad'
                  items={roles}
                  itemHeight={65}
                  header={
                    <Row className='table-header px-3'>
                      <div
                        style={{
                          width: rolesWidths[0],
                        }}
                      >
                        Roles
                      </div>
                      <div
                        style={{
                          width: rolesWidths[1],
                        }}
                      >
                        Description
                      </div>
                    </Row>
                  }
                  renderRow={(role) => (
                    <Row
                      className='list-item clickable cursor-pointer'
                      key={role.id}
                    >
                      <Row
                        onClick={() => editRolePermissions(role)}
                        className='table-column px-3'
                        style={{
                          width: rolesWidths[0],
                        }}
                      >
                        {role.name}
                      </Row>
                      <Row
                        className='table-column px-3'
                        onClick={() => editRolePermissions(role)}
                        style={{
                          width: rolesWidths[1],
                        }}
                      >
                        {role.description}
                      </Row>
                    </Row>
                  )}
                  renderNoResults={
                    <Panel title={'Roles'} className='no-pad'>
                      <div className='search-list'>
                        <Row className='list-item p-3 text-muted'>
                          {`You currently have no roles with ${level} permissions.`}
                        </Row>
                      </div>
                    </Panel>
                  }
                  isLoading={false}
                />
              </>
            ) : (
              <div className='mt-4'>
                <InfoMessage>
                  To use <strong>role</strong> features you have to upgrade your
                  plan.
                </InfoMessage>
              </div>
            )}
          </TabItem>
        )}
      </Tabs>
    </div>
  )
}

export default ConfigProvider(EditPermissions) as unknown as FC<
  Omit<EditPermissionsType, 'router'>
>
