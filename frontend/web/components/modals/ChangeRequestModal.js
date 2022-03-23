import React, { Component } from 'react';
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
        approvals:[]
    }

    addOwner = (id) => {
        this.setState({ approvals: (this.state.approvals || []).concat(id) });
    }

    removeOwner = (id) => {
        this.setState({ approvals: (this.state.approvals || []).filter(v => v !== id) });
    }

    getApprovals = (users, approvals) => users.filter(v => approvals.includes(v.id))

    save = () => {
        const { title, description, approvals } = this.state;
        this.props.onSave({
            title, description, approvals: approvals.map((user)=>({user, required:false})),
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
                            <UserSelect
                              users={users} value={this.state.approvals}
                              onAdd={this.addOwner}
                              onRemove={this.removeOwner}
                              isOpen={this.state.showUsers} onToggle={() => this.setState({ showUsers: !this.state.showUsers })}
                            />

                            <FormGroup className="text-right mt-2">
                                <Button
                                  id="confirm-cancel-plan"
                                  className="btn btn-primary"
                                  disabled={!title || !this.state.approvals.length}
                                  onClick={this.save}
                                >
                                    Create
                                </Button>
                            </FormGroup>
                        </div>);
                }}
            </OrganisationProvider>
        );
    }
};

export default ChangeRequestModal;
