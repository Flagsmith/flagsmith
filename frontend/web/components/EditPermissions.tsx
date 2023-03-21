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
const OrganisationProvider = require('common/providers/OrganisationProvider')
const AppActions = require('common/dispatcher/app-actions')
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import Format from 'common/utils/format'
const Project = require('common/project')
import PanelSearch from './PanelSearch'
import Button, { ButtonLink } from './base/forms/Button'
import InfoMessage from './InfoMessage'
import Switch from './Switch'
import TabItem from './base/forms/TabItem'
import Tabs from './base/forms/Tabs'
import UserGroupList from './UserGroupList'
import { PermissionLevel } from 'common/types/requests'
import { RouterChildContext } from 'react-router'
import { useGetAvailablePermissionsQuery } from 'common/services/useAvailablePermissions'
import ConfigProvider from 'common/providers/ConfigProvider'

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
  const [error, setError] = useState(false)
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
    user,
  } = props

  const { data: permissions } = useGetAvailablePermissionsQuery({ level })

  useEffect(() => {
    let parentGet = Promise.resolve()
    const processResults = (results: (UserPermission & GroupPermission)[]) => {
      let entityPermissions: Omit<EntityPermissions, 'user' | 'group'> & {
        user?: any
        group?: any
      } = isGroup
        ? find(results, (r) => r.group.id === group?.id)!
        : find(results, (r) => r.user?.id === user?.id)!

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
    if (parentLevel) {
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
      .catch((e) => {
        setSaving(false)
        setError(e)
      })
  }

  const togglePermission = (key: string) => {
    const newEntityPermissions = { ...entityPermissions }
    const index = newEntityPermissions.permissions.indexOf(key)
    if (index === -1) {
      newEntityPermissions.permissions.push(key)
    } else {
      newEntityPermissions.permissions.splice(index, 1)
    }
    setEntityPermissions(newEntityPermissions)
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
    <div className='text-center'>
      <Loader />
    </div>
  ) : (
    <div>
      <div className='list-item'>
        {level !== 'organisation' && (
          <Row>
            <Flex>
              <strong>Administrator</strong>
              <div className='list-item-footer faint'>
                {hasRbacPermission ? (
                  `Full View and Write permissions for the given ${Format.camelCase(
                    level,
                  )}.`
                ) : (
                  <span>
                    Role-based access is not available on our Free Plan. Please
                    visit{' '}
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
      <div className='panel--grey'>
        <PanelSearch
          title='Permissions'
          className='no-pad'
          items={permissions}
          renderRow={(p: AvailablePermission) => {
            const levelUpperCase = level.toUpperCase()
            const disabled =
              level !== 'organisation' &&
              p.key !== `VIEW_${levelUpperCase}` &&
              !hasPermission(`VIEW_${levelUpperCase}`)
            return (
              <div
                key={p.key}
                style={admin() ? { opacity: 0.5 } : undefined}
                className='list-item'
              >
                <Row>
                  <Flex>
                    <strong>{Format.enumeration.get(p.key)}</strong>
                    <div className='list-item-footer faint'>
                      {p.description}
                    </div>
                  </Flex>
                  <Switch
                    onChange={() => togglePermission(p.key)}
                    disabled={disabled || admin() || !hasRbacPermission}
                    checked={!disabled && hasPermission(p.key)}
                  />
                </Row>
              </div>
            )
          }}
        />
      </div>

      <p className='text-right mt-2'>
        This will edit the permissions for{' '}
        <strong>{isGroup ? `the ${name} group` : ` ${name}`}</strong>.
      </p>

      {parentError && (
        <InfoMessage>
          The selected {isGroup ? 'group' : 'user'} does not have explicit user
          permissions to view this {parentLevel}. If the user does not belong to
          any groups with this permissions, you may have to adjust their
          permissions in{' '}
          <a
            onClick={() => {
              push(parentSettingsLink!)
              closeModal()
            }}
          >
            <strong>{parentLevel} settings</strong>
          </a>
          .
        </InfoMessage>
      )}
      <div className='text-right'>
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
  useEffect(() => {
    AppActions.getGroups(AccountStore.getOrganisation().id)
  }, [])
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
    )
  }

  return (
    <div className='mt-4'>
      <h3>Manage Users and Permissions</h3>
      <p>
        Flagsmith lets you manage fine-grained permissions for your projects and
        environments.{' '}
        <ButtonLink
          href='https://docs.flagsmith.com/advanced-use/permissions'
          target='_blank'
        >
          Learn about User Roles.
        </ButtonLink>
      </p>
      <Tabs value={tab} onChange={setTab}>
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
                          title=''
                          className='panel--transparent'
                          items={users}
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
                                <div>
                                  <strong>
                                    {`${first_name} ${last_name}`}
                                  </strong>{' '}
                                  {id == AccountStore.getUserId() && '(You)'}
                                  <div className='list-item-footer faint'>
                                    {email}
                                  </div>
                                </div>
                                {role === 'ADMIN' ? (
                                  <Tooltip
                                    html
                                    title='Organisation Administrator'
                                  >
                                    {
                                      'Organisation administrators have all permissions enabled.<br/>To change the role of this user, visit Organisation Settings.'
                                    }
                                  </Tooltip>
                                ) : (
                                  <div onClick={onClick} className='flex-row'>
                                    <span className='mr-3'>
                                      {matchingPermissions &&
                                      matchingPermissions.admin
                                        ? `${Format.camelCase(
                                            level,
                                          )} Administrator`
                                        : 'Regular User'}
                                    </span>
                                    <span
                                      style={{ fontSize: 24 }}
                                      className='icon--primary ion ion-md-settings'
                                    />
                                  </div>
                                )}
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
