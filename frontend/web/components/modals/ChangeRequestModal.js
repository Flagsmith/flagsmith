import React, { Component } from 'react';
import DatePicker from 'react-datepicker';
import UserSelect from '../UserSelect';
import data from '../../../common/data/base/_data';
import OrganisationProvider from '../../../common/providers/OrganisationProvider';
import Button from '../base/forms/Button';

const ChangeRequestModal = class extends Component {
    static displayName = 'ChangeRequestModal'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    state = {
        approvals: (this.props.changeRequest && this.props.changeRequest.approvals) || [],
        title: this.props.changeRequest && this.props.changeRequest.title || '',
        description: this.props.changeRequest && this.props.changeRequest.description || '',
    }

    addOwner = (id) => {
        this.setState({ approvals: (this.state.approvals || []).concat({ user: id }) });
    }

    removeOwner = (id) => {
        this.setState({ approvals: (this.state.approvals || []).filter(v => v.user !== id) });
    }

    getApprovals = (users, approvals) => users.filter(v => approvals.find(a => a.user === v.id))

    save = () => {
        const { title, description, approvals, live_from } = this.state;
        this.props.onSave({
            title, description, approvals, live_from: live_from || undefined,
        });
    }

    render() {
        const { title, description } = this.state;
        return (
            <OrganisationProvider>
                {({ isLoading, name, error, projects, usage, users, invites, influx_data, inviteLinks }) => {
                    const ownerUsers = this.getApprovals(users, this.state.approvals || []);
                    return (
                        <div>
                            <FormGroup className="mb-4" >
                                <InputGroup
                                  value={this.state.title}
                                  onChange={e => this.setState({ title: Utils.safeParseEventValue(e) })}
                                  isValid={title && title.length}
                                  type="text"
                                  title="Title"
                                  inputProps={{ className: 'full-width' }}
                                  className="full-width"
                                  placeholder="My Change Request"
                                />
                            </FormGroup>
                            <FormGroup className="mb-4" >
                                <InputGroup
                                  textarea
                                  value={description}
                                  onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                                  type="text"
                                  title="Description"
                                  inputProps={{ className: 'full-width', style: { minHeight: 80 } }}
                                  className="full-width"
                                  placeholder="Add an optional description..."
                                />
                            </FormGroup>
                            {flagsmith.hasFeature('scheduling') && (
                                <div>
                                    <InputGroup
                                      tooltip="Allows you to set a date and time in which your change will only become active "
                                      title="Schedule Change"
                                      component={(
                                          <Row>
                                              <Flex>
                                                  <DatePicker
                                                      de
                                                    minDate={new Date()} onChange={(e) => {
                                                        this.setState({
                                                            live_from: e.toISOString(),
                                                        });
                                                    }} showTimeInput
                                                      selected={moment(this.state.live_from)._d}
                                                    value={this.state.live_from ? `${moment(this.state.live_from).format('Do MMM YYYY hh:mma')} (${Intl.DateTimeFormat().resolvedOptions().timeZone})` : 'Immediately'}
                                                  />
                                              </Flex>

                                              <ButtonLink className="ml-2" onClick={() => this.setState({ live_from: null })}>
                                                    Clear
                                              </ButtonLink>
                                          </Row>
                                            )}
                                    />
                                </div>
                            )}
                            {!this.props.changeRequest && this.props.showAssignees && (
                                <FormGroup className="mb-4" >
                                    <InputGroup
                                      component={(
                                          <div>
                                              <Row>
                                                  {ownerUsers.map(u => (
                                                      <Row onClick={() => this.removeOwner(u.id)} className="chip chip--active">
                                                          <span className="font-weight-bold">
                                                              {u.first_name} {u.last_name}
                                                          </span>
                                                          <span className="chip-icon ion ion-ios-close"/>
                                                      </Row>
                                                  ))}
                                                  <Button className="btn--link btn--link-primary" onClick={() => this.setState({ showUsers: true })}>Add Assignee</Button>
                                              </Row>

                                          </div>
                                        )}
                                      onChange={e => this.setState({ description: Utils.safeParseEventValue(e) })}
                                      type="text"
                                      title="Assignees"
                                      tooltipPlace="top"
                                      tooltip="Assignees will be able to review and approve the change request"
                                      inputProps={{ className: 'full-width', style: { minHeight: 80 } }}
                                      className="full-width"
                                      placeholder="Add an optional description..."
                                    />
                                </FormGroup>
                            )}
                            {!this.props.changeRequest && (
                                <UserSelect
                                  users={users.filter(v => v.id !== AccountStore.getUser().id)} value={this.state.approvals.map(v => v.user)}
                                  onAdd={this.addOwner}
                                  onRemove={this.removeOwner}
                                  isOpen={this.state.showUsers} onToggle={() => this.setState({ showUsers: !this.state.showUsers })}
                                />
                            )}


                            <FormGroup className="text-right mt-2">
                                <Button
                                  id="confirm-cancel-plan"
                                  className="btn btn-primary"
                                  disabled={!title || (!this.state.approvals.length && (!this.props.changeRequest && this.props.showAssignees))}
                                  onClick={this.save}
                                >
                                    {this.props.changeRequest ? 'Update' : 'Create'}
                                </Button>
                            </FormGroup>
                        </div>);
                }}
            </OrganisationProvider>
        );
    }
};

export default ChangeRequestModal;
