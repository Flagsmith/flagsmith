import React, { Component } from 'react'
import DatePicker from 'react-datepicker'
import UserSelect from 'components/UserSelect'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import Button from 'components/base/forms/Button'
import MyGroupsSelect from 'components/MyGroupsSelect'
import { getMyGroups } from 'common/services/useMyGroup'
import { getStore } from 'common/store'

const ChangeRequestModal = class extends Component {
  static displayName = 'ChangeRequestModal'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  state = {
    approvals:
      (this.props.changeRequest && this.props.changeRequest.approvals) || [],
    description:
      (this.props.changeRequest && this.props.changeRequest.description) || '',
    groups: [],
    live_from:
      this.props.changeRequest &&
      this.props.changeRequest.feature_states[0].live_from,
    title: (this.props.changeRequest && this.props.changeRequest.title) || '',
  }

  componentDidMount() {
    getMyGroups(getStore(), { orgId: AccountStore.getOrganisation().id }).then(
      (res) => {
        this.setState({ groups: res?.data?.results || [] })
      },
    )
  }

  addOwner = (id, isUser = true) => {
    this.setState({
      approvals: (this.state.approvals || []).concat(
        isUser ? { user: id } : { group: id },
      ),
    })
  }

  removeOwner = (id, isUser = true) => {
    this.setState({
      approvals: (this.state.approvals || []).filter((v) =>
        isUser ? v.user !== id : v.group !== id,
      ),
    })
  }

  getApprovals = (users, approvals) =>
    users.filter((v) => approvals.find((a) => a.user === v.id))

  getGroupApprovals = (groups, approvals) =>
    groups.filter((v) => approvals.find((a) => a.group === v.id))

  save = () => {
    const { approvals, description, live_from, title } = this.state
    this.props.onSave({
      approvals,
      description,
      live_from: live_from || undefined,
      title,
    })
  }

  render() {
    const { description, groups, title } = this.state
    return (
      <OrganisationProvider>
        {({ users }) => {
          const ownerGroups = this.getGroupApprovals(
            groups,
            this.state.approvals || [],
          )
          const ownerUsers = this.getApprovals(
            users,
            this.state.approvals || [],
          )
          return (
            <div>
              <FormGroup className='mb-4'>
                <InputGroup
                  value={this.state.title}
                  onChange={(e) =>
                    this.setState({ title: Utils.safeParseEventValue(e) })
                  }
                  isValid={title && title.length}
                  type='text'
                  title='Title'
                  inputProps={{ className: 'full-width' }}
                  className='full-width'
                  placeholder='My Change Request'
                />
              </FormGroup>
              <FormGroup className='mb-4'>
                <InputGroup
                  textarea
                  value={description}
                  onChange={(e) =>
                    this.setState({ description: Utils.safeParseEventValue(e) })
                  }
                  type='text'
                  title='Description'
                  inputProps={{
                    className: 'full-width',
                    style: { minHeight: 80 },
                  }}
                  className='full-width'
                  placeholder='Add an optional description...'
                />
              </FormGroup>
              <div>
                <InputGroup
                  tooltip='Allows you to set a date and time in which your change will only become active '
                  title='Schedule Change'
                  component={
                    <Row>
                      <Flex>
                        <DatePicker
                          minDate={new Date()}
                          onChange={(e) => {
                            this.setState({
                              live_from: e.toISOString(),
                            })
                          }}
                          showTimeInput
                          selected={moment(this.state.live_from)._d}
                          value={
                            this.state.live_from
                              ? `${moment(this.state.live_from).format(
                                  'Do MMM YYYY hh:mma',
                                )} (${
                                  Intl.DateTimeFormat().resolvedOptions()
                                    .timeZone
                                })`
                              : 'Immediately'
                          }
                        />
                      </Flex>

                      <Button
                        theme='text'
                        className='ml-2'
                        onClick={() => {
                          this.setState({ live_from: null })
                        }}
                      >
                        Clear
                      </Button>
                    </Row>
                  }
                />
              </div>
              {!this.props.changeRequest &&
                this.props.showAssignees &&
                (!Utils.getFlagsmithHasFeature('disable_users_as_reviewers') ||
                  Utils.getFlagsmithHasFeature(
                    'enable_groups_as_reviewers',
                  )) && (
                  <FormGroup className='mb-4'>
                    <InputGroup
                      component={
                        <div>
                          {!Utils.getFlagsmithHasFeature(
                            'disable_users_as_reviewers',
                          ) && (
                            <Row>
                              <strong style={{ width: 70 }}> Users: </strong>
                              {ownerUsers.map((u) => (
                                <Row
                                  key={u.id}
                                  onClick={() => this.removeOwner(u.id)}
                                  className='chip chip--active'
                                  style={{ marginBottom: 4, marginTop: 4 }}
                                >
                                  <span className='font-weight-bold'>
                                    {u.first_name} {u.last_name}
                                  </span>
                                  <span className='chip-icon ion ion-ios-close' />
                                </Row>
                              ))}
                              <Button
                                theme="text"
                                onClick={() =>
                                  this.setState({ showUsers: true })
                                }
                              >
                                Add user
                              </Button>
                            </Row>
                          )}
                          {Utils.getFlagsmithHasFeature(
                            'enable_groups_as_reviewers',
                          ) && (
                            <Row>
                              <strong style={{ width: 70 }}> Groups: </strong>
                              {ownerGroups.map((u) => (
                                <Row
                                  key={u.id}
                                  onClick={() => this.removeOwner(u.id, false)}
                                  className='chip chip--active'
                                  style={{ marginBottom: 4, marginTop: 4 }}
                                >
                                  <span className='font-weight-bold'>
                                    {u.name}
                                  </span>
                                  <span className='chip-icon ion ion-ios-close' />
                                </Row>
                              ))}
                              <Button
                                theme="text"
                                onClick={() =>
                                  this.setState({ showGroups: true })
                                }
                              >
                                Add group
                              </Button>
                            </Row>
                          )}
                        </div>
                      }
                      onChange={(e) =>
                        this.setState({
                          description: Utils.safeParseEventValue(e),
                        })
                      }
                      type='text'
                      title='Assignees'
                      tooltipPlace='top'
                      tooltip='Assignees will be able to review and approve the change request'
                      inputProps={{
                        className: 'full-width',
                        style: { minHeight: 80 },
                      }}
                      className='full-width'
                      placeholder='Add an optional description...'
                    />
                  </FormGroup>
                )}
              {!this.props.changeRequest &&
                !Utils.getFlagsmithHasFeature('disable_users_as_reviewers') && (
                  <UserSelect
                    users={users.filter(
                      (v) => v.id !== AccountStore.getUser().id,
                    )}
                    value={this.state.approvals.map((v) => v.user)}
                    onAdd={this.addOwner}
                    onRemove={this.removeOwner}
                    isOpen={this.state.showUsers}
                    onToggle={() =>
                      this.setState({ showUsers: !this.state.showUsers })
                    }
                  />
                )}
              {!this.props.changeRequest &&
                Utils.getFlagsmithHasFeature('enable_groups_as_reviewers') && (
                  <MyGroupsSelect
                    orgId={AccountStore.getOrganisation().id}
                    value={this.state.approvals.map((v) => v.group)}
                    onAdd={this.addOwner}
                    onRemove={this.removeOwner}
                    isOpen={this.state.showGroups}
                    onToggle={() =>
                      this.setState({ showGroups: !this.state.showGroups })
                    }
                  />
                )}

              <FormGroup className='text-right mt-2'>
                <Button
                  id='confirm-cancel-plan'
                  className='btn btn-primary'
                  disabled={!title}
                  onClick={this.save}
                >
                  {this.props.changeRequest ? 'Update' : 'Create'}
                </Button>
              </FormGroup>
            </div>
          )
        }}
      </OrganisationProvider>
    )
  }
}

export default ChangeRequestModal
