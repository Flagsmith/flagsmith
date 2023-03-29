import React, { Component } from 'react'
import UserGroupsProvider from 'common/providers/UserGroupsProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Switch from 'components/Switch'

const CreateGroup = class extends Component {
  static displayName = 'CreateGroup'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {
      external_id: props.group ? props.group.external_id : undefined,
      is_default: props.group ? props.group.is_default : false,
      name: props.group ? props.group.name : '',
      users: props.group ? props.group.users : [],
    }
  }

  close() {
    closeModal()
  }

  componentDidMount = () => {
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

  save = (allUsers) => {
    const { external_id, is_default, name, users } = this.state
    if (this.props.group) {
      AppActions.updateGroup(this.props.orgId, {
        external_id,
        id: this.props.group.id,
        is_default: !!this.state.is_default,
        name,
        users,
        usersToRemove: this.getUsersToRemove(allUsers),
      })
    } else {
      AppActions.createGroup(this.props.orgId, {
        external_id,
        is_default,
        name,
        users,
        usersToRemove: this.getUsersToRemove(allUsers),
      })
    }
  }

  toggleUser = (id) => {
    const isMember = _.find(this.state.users, { id })
    const users = _.filter(this.state.users, (u) => u.id !== id)
    this.setState({ users: isMember ? users : users.concat([{ id }]) })
  }

  render() {
    const { external_id, name } = this.state
    const isEdit = !!this.props.group
    const isAdmin = AccountStore.isAdmin()
    const yourEmail = AccountStore.model.email
    return (
      <OrganisationProvider>
        {({ users }) => (
          <UserGroupsProvider onSave={this.close}>
            {({ isSaving }) => (
              <form
                onSubmit={(e) => {
                  Utils.preventDefault(e)
                  this.save(users)
                }}
              >
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
                    this.setState({ name: Utils.safeParseEventValue(e) })
                  }
                  isValid={name && name.length}
                  type='text'
                  name='Name*'
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
                    this.setState({ external_id: Utils.safeParseEventValue(e) })
                  }
                  isValid={name && name.length}
                  type='text'
                  name='Name*'
                  placeholder='Add an optional external reference ID'
                />

                <InputGroup
                  title='Add new users by default'
                  tooltipPlace='top'
                  tooltip='New users that sign up to your organisation will be automatically added to this group with USER permissions'
                  ref={(e) => (this.input = e)}
                  data-test='groupName'
                  component={
                    <Switch
                      onChange={(e) =>
                        this.setState({
                          is_default: Utils.safeParseEventValue(e),
                        })
                      }
                      checked={!!this.state.is_default}
                    />
                  }
                  inputProps={{
                    className: 'full-width',
                    name: 'groupName',
                  }}
                  value={name}
                  isValid={name && name.length}
                  type='text'
                />
                <div className='mb-5'>
                  <PanelSearch
                    id='org-members-list'
                    title='Members'
                    className='mt-5 no-pad'
                    items={_.sortBy(users, 'first_name')}
                    filterRow={(item, search) => {
                      const strToSearch = `${item.first_name} ${item.last_name} ${item.id}`
                      return (
                        strToSearch
                          .toLowerCase()
                          .indexOf(search.toLowerCase()) !== -1
                      )
                    }}
                    renderRow={({ email, first_name, id, last_name }) => (
                      <Row space className='list-item' key={id}>
                        <div>
                          {`${first_name} ${last_name}`}{' '}
                          {id == AccountStore.getUserId() && '(You)'}
                          <div className='list-item-footer faint'>{email}</div>
                        </div>
                        <Switch
                          disabled={!(isAdmin || email !== yourEmail)}
                          onChange={() => this.toggleUser(id)}
                          checked={!!_.find(this.state.users, { id })}
                        />
                      </Row>
                    )}
                  />
                </div>
                <div className='text-right'>
                  {isEdit ? (
                    <Button
                      data-test='update-feature-btn'
                      id='update-feature-btn'
                      disabled={isSaving || !name}
                    >
                      {isSaving ? 'Updating' : 'Update Group'}
                    </Button>
                  ) : (
                    <Button
                      data-test='create-feature-btn'
                      id='create-feature-btn'
                      disabled={isSaving || !name}
                    >
                      {isSaving ? 'Creating' : 'Create Group'}
                    </Button>
                  )}
                </div>
              </form>
            )}
          </UserGroupsProvider>
        )}
      </OrganisationProvider>
    )
  }
}

CreateGroup.propTypes = {}

module.exports = ConfigProvider(CreateGroup)
