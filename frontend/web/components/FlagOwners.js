import React, { Component } from 'react';
import { ListItem } from '@material-ui/core';
import data from '../../common/data/base/_data';
import UserSelect from './UserSelect';
import AuditLogIcon from './svg/AuditLogIcon';

class TheComponent extends Component {
    state = {};

    componentDidMount() {
        this.getData();
    }

    getData = () => {
        data.get(`${Project.api}projects/${this.props.projectId}/features/${this.props.id}/`)
            .then((res) => {
                const owners = (res.owners || []).map(v => v.id);
                this.setState({ owners });
            });
    }

    addOwner = (id) => {
        this.setState({ owners: (this.state.owners || []).concat(id) });
        data.post(`${Project.api}projects/${this.props.projectId}/features/${this.props.id}/add-owners/`, {
            user_ids: [id],
        });
    }

    removeOwner = (id) => {
        this.setState({ owners: (this.state.owners || []).filter(v => v !== id) });
        data.post(`${Project.api}projects/${this.props.projectId}/features/${this.props.id}/remove-owners/`, {
            user_ids: [id],
        });
    }

    getOwners = (users, owners) => users.filter(v => owners.includes(v.id))

    render() {
        const hasPermission = !this.props.hasFeature('plan_based_access') || Utils.getPlansPermission('FLAG_OWNERS');

        return (
            <OrganisationProvider>
                {({ isLoading, name, error, projects, usage, users, invites, influx_data, inviteLinks }) => {
                    const ownerUsers = this.getOwners(users, this.state.owners || []);
                    const res = (
                        <div>
                            <Row
                              className="clickable" onClick={() => {
                                  if (hasPermission) this.setState({ showUsers: true });
                              }}
                            >
                                <label className="cols-sm-2 control-label">Assignees</label>
                                <span
                                  style={{
                                      marginBottom: '0.5rem',
                                  }} className="icon ml-5 ion-md-cog icon-primary"
                                />
                            </Row>
                            <Row>
                                {hasPermission && ownerUsers.map(u => (
                                    <Row onClick={() => this.removeOwner(u.id)} className="chip chip--active">
                                        <span className="font-weight-bold">
                                            {u.first_name} {u.last_name}
                                        </span>
                                        <span className="chip-icon ion ion-ios-close"/>

                                    </Row>
                                ))}
                                {!ownerUsers.length && (
                                    <div>
                                        This flag has no assignees
                                    </div>
                                )}
                            </Row>

                            <UserSelect
                              users={users} value={this.state.owners}
                              onAdd={this.addOwner}
                              onRemove={this.removeOwner}
                              isOpen={this.state.showUsers} onToggle={() => this.setState({ showUsers: !this.state.showUsers })}
                            />

                        </div>
                    );
                    return hasPermission ? res : (
                        <Tooltip
                          title={res}
                        >
                            The add flag assignees feature is available with our startup plan
                        </Tooltip>
                    );
                }}
            </OrganisationProvider>
        );
    }
}

export default hot(module)(ConfigProvider(TheComponent));
