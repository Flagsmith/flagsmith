import React, { Component } from 'react'
import UserGroupsProvider from 'common/providers/UserGroupsProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Switch from 'components/Switch'
import { getGroup } from 'common/services/useGroup'
import { getStore } from 'common/store'
import { components } from 'react-select'
import { setInterceptClose } from './base/ModalDefault'
import Icon from 'components/Icon'
import Tooltip from 'components/Tooltip'

const widths = [80, 80]
const CreateGroup = class extends Component {
  static displayName = 'CreateGroup'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {
      externalIdEdited: false,
      groupNameEdited: false,
      isLoading: !!this.props.group,
      toggleChange: false,
      userAddedOrUpdated: false,
      userRemoved: false,
    }
    if (this.props.group) {
      this.loadGroup()
    }
  }

  loadGroup = () => {
    getGroup(
      getStore(),
      {
        id: this.props.group.id,
        orgId: this.props.orgId,
      },
      { forceRefetch: true },
    ).then((res) => {
      const group = res.data
      this.setState({
        existingUsers: group
          ? group.users.map((v) => ({
              group_admin: v.group_admin,
              id: v.id,
            }))
          : [],
        external_id: group ? group.external_id : undefined,
        isLoading: false,
        is_default: group ? group.is_default : false,
        name: group ? group.name : '',
        users: group
          ? group.users.map((v) => ({
              edited: false,
              group_admin: v.group_admin,
              id: v.id,
            }))
          : [],
      })
    })
  }
  close() {
    closeModal()
  }

  onClosing = () => {
    if (
      this.state.groupNameEdited ||
      this.state.externalIdEdited ||
      this.state.toggleChange ||
      this.state.userAddedOrUpdated ||
      this.state.userRemoved
    ) {
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
  }

  componentDidMount = () => {
    if (this.props.isEdit) {
      setInterceptClose(this.onClosing)
    }
    if (!this.props.isEdit && !E2E) {
      this.focusTimeout = setTimeout(() => {
        this.input.focus()
        this.focusTimeout = null
      }, 500)
    }
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  getUsersToRemove = (users) =>
    _.filter(users, ({ id }) => !_.find(this.state.users, { id }))

  getUsersAdminChanged = (existingUsers, value) => {
    return _.filter(this.state.users, (user) => {
      if (!!user.group_admin !== value) {
        //Ignore user
        return false
      }
      const existingUser = _.find(
        existingUsers,
        (existingUser) => existingUser.id === user.id,
      )
      const isAlreadyAdmin = !!existingUser?.group_admin

      return isAlreadyAdmin !== value
    })
  }

  save = () => {
    const { external_id, name, users } = this.state

    this.setState({
      externalIdEdited: false,
      groupNameEdited: false,
      toggleChange: false,
      userAddedOrUpdated: false,
      userRemoved: false,
    })
    const data = {
      external_id,
      is_default: !!this.state.is_default,
      name,
      users,
      usersToAddAdmin: this.getUsersAdminChanged(
        this.state.existingUsers,
        true,
      ),
    }
    if (this.props.group) {
      AppActions.updateGroup(this.props.orgId, {
        ...data,
        id: this.props.group.id,
        usersToRemove: this.getUsersToRemove(this.state.existingUsers),
        usersToRemoveAdmin: this.getUsersAdminChanged(
          this.state.existingUsers,
          false,
        ),
      })
    } else {
      AppActions.createGroup(this.props.orgId, data)
    }
  }

  toggleUser = (id, group_admin, update) => {
    const isMember = _.find(this.state.users, { id })
    const users = _.filter(this.state.users, (u) => u.id !== id)
    this.setState({
      userAddedOrUpdated: true,
      users:
        isMember && !update
          ? users
          : users.concat([{ edited: true, group_admin, id }]),
    })
  }

  render() {
    const { external_id, isLoading, name } = this.state
    const isEdit = !!this.props.group
    const isAdmin = AccountStore.isAdmin()
    const yourEmail = AccountStore.model.email
    return (
      <OrganisationProvider>
        {({ users }) => {
          const activeUsers = _.intersectionBy(users, this.state.users, 'id')
          const inactiveUsers = _.differenceBy(users, this.state.users, 'id')
          return isLoading ? (
            <div className='text-center'>
              <Loader />
            </div>
          ) : (
            <UserGroupsProvider onSave={this.close}>
              {({ isSaving }) => (
                <form
                  className='create-feature-tab'
                  onSubmit={(e) => {
                    Utils.preventDefault(e)
                    this.save()
                  }}
                >
                  <FormGroup className='my-4 mx-3'>
                    <InputGroup
                      title='Group name*'
                      ref={(e) => (this.input = e)}
                      data-test='groupName'
                      inputProps={{
                        className: 'full-width',
                        name: 'groupName',
                      }}
                      value={name}
                      onChange={(e) =>
                        this.setState({
                          groupNameEdited: true,
                          name: Utils.safeParseEventValue(e),
                        })
                      }
                      isValid={name && name.length}
                      type='text'
                      name='Name*'
                      unsaved={this.props.isEdit && this.state.groupNameEdited}
                      placeholder='E.g. Developers'
                    />
                    <InputGroup
                      title='External ID'
                      ref={(e) => (this.input = e)}
                      data-test='groupName'
                      inputProps={{
                        className: 'full-width',
                        name: 'groupName',
                      }}
                      value={external_id}
                      onChange={(e) =>
                        this.setState({
                          externalIdEdited: true,
                          external_id: Utils.safeParseEventValue(e),
                        })
                      }
                      isValid={name && name.length}
                      type='text'
                      name='Name*'
                      unsaved={this.props.isEdit && this.state.externalIdEdited}
                      placeholder='Add an optional external reference ID'
                    />

                    <Row className='mb-4'>
                      <Tooltip
                        title={
                          <Row>
                            <Switch
                              onChange={(e) =>
                                this.setState({
                                  is_default: Utils.safeParseEventValue(e),
                                  toggleChange: true,
                                })
                              }
                              checked={!!this.state.is_default}
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

                    <div className='mb-4'>
                      <label>Group members</label>
                      <div>
                        <Select
                          disabled={!inactiveUsers?.length}
                          components={{
                            Option: (props) => {
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
                          onChange={(v) => this.toggleUser(v.value)}
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
                        noResultsText={(search) =>
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
                        items={_.sortBy(activeUsers, 'first_name')}
                        filterRow={(item, search) => {
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
                                <div>
                                  User{' '}
                                  {this.props.isEdit &&
                                    this.state.userRemoved && (
                                      <div className='unread'>Unsaved</div>
                                    )}
                                </div>
                              </Flex>
                              {Utils.getFlagsmithHasFeature('group_admins') && (
                                <div
                                  style={{ paddingLeft: 5, width: widths[0] }}
                                  className='table-column'
                                >
                                  Admin
                                </div>
                              )}
                              <div
                                className='table-column text-center'
                                style={{ width: widths[1] }}
                              >
                                Remove
                              </div>
                            </Row>
                          </>
                        }
                        renderRow={({ email, first_name, id, last_name }) => {
                          const matchingUser = this.state.users.find(
                            (v) => v.id === id,
                          )
                          const isGroupAdmin = matchingUser?.group_admin
                          const userEdited = matchingUser?.edited
                          return (
                            <Row className='list-item' key={id}>
                              <Flex className='table-column px-3'>
                                <div className='font-weight-medium'>
                                  {`${first_name} ${last_name}`}{' '}
                                  {id == AccountStore.getUserId() && '(You)'}{' '}
                                  {this.props.isEdit && userEdited && (
                                    <div className='unread'>Unsaved</div>
                                  )}
                                </div>
                                <div className='list-item-subtitle mt-1'>
                                  {email}
                                </div>
                              </Flex>
                              {Utils.getFlagsmithHasFeature('group_admins') && (
                                <div style={{ width: widths[0] }}>
                                  <Switch
                                    onChange={(e) => {
                                      this.toggleUser(id, e, true)
                                    }}
                                    checked={isGroupAdmin}
                                  />
                                </div>
                              )}
                              <div
                                className='table-column text-center'
                                style={{ width: widths[1] }}
                              >
                                <Button
                                  type='button'
                                  disabled={!(isAdmin || email !== yourEmail)}
                                  id='remove-feature'
                                  onClick={() => {
                                    this.toggleUser(id)
                                    this.setState({ userRemoved: true })
                                  }}
                                  className='btn btn-with-icon'
                                >
                                  <Icon
                                    name='trash-2'
                                    width={20}
                                    fill='#656D7B'
                                  />
                                </Button>
                              </div>
                            </Row>
                          )
                        }}
                      />
                    </div>
                    <div className='text-right'>
                      {isEdit ? (
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
              )}
            </UserGroupsProvider>
          )
        }}
      </OrganisationProvider>
    )
  }
}

CreateGroup.propTypes = {}

module.exports = ConfigProvider(CreateGroup)
