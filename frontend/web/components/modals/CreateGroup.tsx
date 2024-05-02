import React, { FC, useCallback, useEffect, useState } from 'react'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Switch from 'components/Switch'
import {
  useCreateGroupMutation,
  useGetGroupQuery,
  useUpdateGroupMutation,
} from 'common/services/useGroup'
import { components } from 'react-select'
import { setInterceptClose } from './base/ModalDefault'
import Icon from 'components/Icon'
import Tooltip from 'components/Tooltip'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import AppActions from 'common/dispatcher/app-actions'
import { GroupUser, Role, User, UserGroupSummary } from 'common/types/responses'
import { differenceBy, find, intersectionBy, sortBy } from 'lodash'
import filter from 'lodash/filter'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import AccountStore from 'common/stores/account-store'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import { Req } from 'common/types/requests'
import PermissionsTabs from 'components/PermissionsTabs'

const widths = [80, 80]

type CreateGroupType = {
  roles?: Role[]
  group: UserGroupSummary
  orgId: string
}

const CreateGroup: FC<CreateGroupType> = ({ group, orgId, roles }) => {
  const [edited, setEdited] = useState(false)
  const [externalId, setExternalId] = useState('')
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(!!group)
  const [existingUsers, setExistingUsers] = useState<GroupUser[]>([])
  const [isDefault, setIsDefault] = useState(false)
  const [createGroup, { isLoading: creatingGroup }] = useCreateGroupMutation({})
  const [updateGroup, { isLoading: updatingGroup }] = useUpdateGroupMutation({})
  const isSaving = creatingGroup || updatingGroup
  const [users, setUsers] = useState<
    {
      edited: boolean
      group_admin: boolean
      id: number
    }[]
  >([])

  const { data: groupData } = useGetGroupQuery(
    { id: `${group?.id}`, orgId },
    { skip: !group || !orgId },
  )
  const onClosing = useCallback(() => {
    if (edited) {
      return new Promise((resolve) => {
        openConfirm({
          body: 'Closing this will discard your unsaved changes.',
          noText: 'Cancel',
          onNo: () => resolve(false),
          onYes: () => resolve(true),
          title: 'Discard changes',
          yesText: 'Ok',
        })
      })
    } else {
      return Promise.resolve(true)
    }
  }, [edited])

  useEffect(() => {
    setInterceptClose(onClosing)
  }, [onClosing])

  useEffect(() => {
    if (groupData) {
      setExistingUsers(groupData.users)
      setUsers(
        (groupData.users || []).map((v) => ({
          edited: false,
          group_admin: v.group_admin,
          id: v.id,
        })),
      )
      setExternalId(groupData.external_id || '')
      setIsLoading(false)
      setIsDefault(groupData.is_default)
      setName(groupData.name)
    }
  }, [groupData])

  useEffect(() => {
    if (!group) {
      setTimeout(() => {
        document.getElementById('groupName')?.focus()
      }, 500)
    }
  }, [group])

  if (!orgId) {
    return null
  }

  const getUsersToRemove = (usersToFilter: GroupUser[]) =>
    filter(usersToFilter, ({ id }) => !find(users, { id }))

  const getUsersAdminChanged = (existingUsers: GroupUser[], value: boolean) => {
    return filter(users, (user) => {
      if (!!user.group_admin !== value) {
        //Ignore user
        return false
      }
      const existingUser = find(
        existingUsers,
        (existingUser) => existingUser.id === user.id,
      )
      const isAlreadyAdmin = !!existingUser?.group_admin

      return isAlreadyAdmin !== value
    })
  }

  const save = () => {
    setInterceptClose(null)
    const usersToAddAdmin = getUsersAdminChanged(existingUsers, true)
    const usersToRemoveAdmin = getUsersAdminChanged(existingUsers, false)
    if (group) {
      const data: Req['updateGroup']['data'] = {
        ...group,
        external_id: externalId || null,
        is_default: isDefault,
        name,
        users: users as any,
      }
      updateGroup({
        data,
        orgId,
        users: users as any,
        usersToAddAdmin: (usersToAddAdmin || []).map((user) => user.id),
        usersToRemove: getUsersToRemove(groupData.users).map((v) => v.id),
        usersToRemoveAdmin: (usersToRemoveAdmin || []).map((user) => user.id),
      }).then((data) => {
        if (!data.error) {
          toast('Updated Group')
          closeModal()
        }
      })
    } else {
      const data: Req['createGroup']['data'] = {
        external_id: externalId || null,
        is_default: isDefault,
        name,
      }
      createGroup({
        data,
        orgId,
        users: users as any,
        usersToAddAdmin: (usersToAddAdmin || []).map((user) => user.id),
      }).then((data) => {
        if (!data.error) {
          toast('Created Group')
          closeModal()
        }
      })
    }
  }

  const toggleUser = (id: number, group_admin: boolean, update: boolean) => {
    const isMember = !!find(existingUsers, { id })
    const newUsers = filter(users, (u) => u.id !== id)!
    setUsers(
      isMember && !update
        ? newUsers
        : newUsers.concat([{ edited: true, group_admin, id }]),
    )
  }

  const isEdit = !!group
  const editGroupEl = (
    <OrganisationProvider>
      {({ users: organisationUsers }) => {
        const activeUsers = intersectionBy(organisationUsers, users, 'id')
        const inactiveUsers = differenceBy(organisationUsers, users, 'id')
        const isAdmin = AccountStore.isAdmin()
        const yourEmail = (AccountStore as { model?: User }).model?.email

        return isLoading ? (
          <div className='text-center'>
            <Loader />
          </div>
        ) : (
          <>
            <form
              className='create-feature-tab'
              onSubmit={(e) => {
                Utils.preventDefault(e)
                save()
              }}
            >
              <FormGroup className='m-4'>
                <InputGroup
                  title='Group name*'
                  data-test='groupName'
                  id='groupName'
                  inputProps={{
                    className: 'full-width',
                    name: 'groupName',
                  }}
                  value={name}
                  onChange={(e: InputEvent) => {
                    setName(Utils.safeParseEventValue(e))
                    setEdited(true)
                  }}
                  isValid={name && name.length}
                  type='text'
                  name='Name*'
                  placeholder='E.g. Developers'
                  className='mb-5'
                />
                <InputGroup
                  title='External ID'
                  tooltip={
                    'The external ID of the group in your SSO provider, used for synchronising users.'
                  }
                  data-test='externalId'
                  inputProps={{
                    className: 'full-width',
                    name: 'groupName',
                  }}
                  value={externalId}
                  onChange={(e: InputEvent) => {
                    setEdited(true)
                    setExternalId(Utils.safeParseEventValue(e))
                  }}
                  isValid={name && name.length}
                  type='text'
                  name='Name*'
                  placeholder='Add an optional external reference ID'
                  className='mb-5'
                />

                <Row className='mb-5'>
                  <Tooltip
                    title={
                      <Row>
                        <Switch
                          onChange={(e: boolean) => {
                            setIsDefault(Utils.safeParseEventValue(e))
                            setEdited(true)
                          }}
                          checked={!!isDefault}
                        />
                        <label className='ms-2 me-2 mb-0'>
                          Add new users by default
                        </label>
                        <Icon name='info-outlined' />
                      </Row>
                    }
                  >
                    New users that sign up to your organisation will be
                    automatically added to this group with USER permissions
                  </Tooltip>
                </Row>

                <div className='mb-5'>
                  <label>Group members</label>
                  <div>
                    <Select
                      disabled={!inactiveUsers?.length}
                      components={{
                        Option: (props: any) => {
                          const { email, first_name, id, last_name } =
                            props.data.user || {}
                          return (
                            <components.Option {...props}>
                              {`${first_name} ${last_name}`}{' '}
                              {id == AccountStore.getUserId() && '(You)'}
                              <div className='list-item-footer faint'>
                                {email}
                              </div>
                            </components.Option>
                          )
                        },
                      }}
                      value={{ label: 'Add a user' }}
                      onChange={(v: { value: number }) => {
                        toggleUser(v.value, false, false)
                        setEdited(true)
                      }}
                      options={inactiveUsers.map((user) => ({
                        label: `${user.first_name || ''} ${
                          user.last_name || ''
                        } ${user.email} ${user.id}`,
                        user,
                        value: user.id,
                      }))}
                    />
                  </div>

                  <PanelSearch
                    noResultsText={(search: string) =>
                      search ? (
                        <Flex className='text-center'>
                          No results found for <strong>{search}</strong>
                        </Flex>
                      ) : (
                        <Flex className='text-center'>
                          This group has no members
                        </Flex>
                      )
                    }
                    id='org-members-list'
                    title='Members'
                    className='mt-4 no-pad overflow-visible'
                    renderSearchWithNoResults
                    items={sortBy(activeUsers, 'first_name')}
                    filterRow={(item: GroupUser, search: string) => {
                      const strToSearch = `${item.first_name} ${item.last_name} ${item.email} ${item.id}`
                      return (
                        strToSearch
                          .toLowerCase()
                          .indexOf(search.toLowerCase()) !== -1
                      )
                    }}
                    header={
                      <>
                        <Row className='table-header'>
                          <Flex className='table-column px-3'>
                            <div>User</div>
                          </Flex>
                          <div
                            style={{ paddingLeft: 5, width: widths[0] }}
                            className='table-column'
                          >
                            <Tooltip
                              title={
                                <Row>
                                  Admin <IonIcon icon={informationCircle} />
                                </Row>
                              }
                            >
                              Allows inviting additional team members to the
                              group
                            </Tooltip>
                          </div>
                          <div
                            className='table-column ml-1 text-center'
                            style={{ width: widths[1] }}
                          >
                            Remove
                          </div>
                        </Row>
                      </>
                    }
                    renderRow={({
                      email,
                      first_name,
                      id,
                      last_name,
                    }: GroupUser) => {
                      const matchingUser = users.find((v) => v.id === id)
                      const isGroupAdmin = matchingUser?.group_admin
                      const userEdited = matchingUser?.edited
                      return (
                        <Row className='list-item' key={id}>
                          <Flex className='table-column px-3'>
                            <div className='font-weight-medium'>
                              {`${first_name} ${last_name}`}{' '}
                              {id == AccountStore.getUserId() && '(You)'}{' '}
                              {isEdit && userEdited && (
                                <div className='unread'>Unsaved</div>
                              )}
                            </div>
                            <div className='list-item-subtitle mt-1'>
                              {email}
                            </div>
                          </Flex>
                          <div style={{ width: widths[0] }}>
                            <Switch
                              onChange={(e: boolean) => {
                                toggleUser(id, e, true)
                                setEdited(true)
                              }}
                              checked={isGroupAdmin}
                            />
                          </div>
                          <div
                            className='table-column text-center'
                            style={{ width: widths[1] }}
                          >
                            <Button
                              type='button'
                              disabled={!(isAdmin || email !== yourEmail)}
                              id='remove-feature'
                              onClick={() => {
                                toggleUser(id, false, false)
                                setEdited(true)
                              }}
                              className='btn btn-with-icon'
                            >
                              <Icon name='trash-2' width={20} fill='#656D7B' />
                            </Button>
                          </div>
                        </Row>
                      )
                    }}
                  />
                </div>
                <div className='text-right'>
                  {group ? (
                    <>
                      <Button type='submit' disabled={isSaving || !name}>
                        {isSaving ? 'Updating' : 'Update Group'}
                      </Button>
                    </>
                  ) : (
                    <Button
                      type='submit'
                      data-test='create-feature-btn'
                      id='create-feature-btn'
                      disabled={isSaving || !name}
                    >
                      {isSaving ? 'Creating' : 'Create Group'}
                    </Button>
                  )}
                </div>
              </FormGroup>
            </form>
          </>
        )
      }}
    </OrganisationProvider>
  )
  const editPermissionsEl = (
    <div className='mt-4'>
      {!!groupData && (
        <PermissionsTabs
          uncontrolled
          orgId={AccountStore.getOrganisation()?.id}
          group={group}
        />
      )}
    </div>
  )
  return isEdit ? (
    <Tabs uncontrolled tabClassName='px-0'>
      <TabItem
        tabLabel={
          <div>
            General
            {!!edited && <span className='unread'>*</span>}
          </div>
        }
      >
        {editGroupEl}
      </TabItem>
      <TabItem tabLabel={<div>Permissions</div>}>{editPermissionsEl}</TabItem>
    </Tabs>
  ) : (
    editGroupEl
  )
}

export default ConfigProvider(CreateGroup)
