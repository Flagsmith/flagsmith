import React, { Component } from 'react';
import ChangeRequestStore from '../../../common/stores/change-requests-store';
import OrganisationStore from '../../../common/stores/organisation-store';
import Button from '../base/forms/Button';
import UserSelect from '../UserSelect';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';

const ChangeRequestsPage = class extends Component {
    static displayName = 'ChangeRequestsPage';

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    getApprovals = (users, approvals) => users.filter(v => approvals.includes(v.id))


    constructor(props, context) {
        super(props, context);
        this.state = {
            tags: [],
            showArchived: false,
        };
        ES6Component(this);
        this.listenTo(ChangeRequestStore, 'change', () => this.forceUpdate());
        this.listenTo(OrganisationStore, 'change', () => this.forceUpdate());
        AppActions.getChangeRequest(this.props.match.params.id);
        AppActions.getOrganisation(AccountStore.getOrganisation().id);
    }

    removeOwner = (id) => {
        if (ChangeRequestStore.isLoading) return;
        const changeRequest = ChangeRequestStore.model[this.props.match.params.id];
        AppActions.updateChangeRequest({
            id: changeRequest.id,
            title: changeRequest.title,
            description: changeRequest.description,
            feature_states: changeRequest.feature_states,
            approvals: changeRequest.approvals.filter(v => v.user !== id),
        });
    }

    addOwner = (id) => {
        if (ChangeRequestStore.isLoading) return;
        const changeRequest = ChangeRequestStore.model[this.props.match.params.id];
        AppActions.updateChangeRequest({
            id: changeRequest.id,
            title: changeRequest.title,
            description: changeRequest.description,
            feature_states: changeRequest.feature_states,
            approvals: changeRequest.approvals.concat([{ user: id, required: false }]),
        });
    }

    componentWillUpdate() {

    }

    componentDidMount = () => {

    };

    deleteChangeRequest = () => {
        openConfirm(<h3>Delete Trait</h3>, (
            <p>
                Are you sure you want to delete this change request?
            </p>
        ), AppActions.deleteChangeRequest(this.props.match.params.id));
    }

    render() {
        const id = this.props.match.params.id;
        const changeRequest = ChangeRequestStore.model[id];
        if (OrganisationStore.isLoading || (ChangeRequestStore.isLoading && !changeRequest)) {
            return (
                <div data-test="change-requests-page" id="change-requests-page" className="app-container container">
                    <div className="text-center"><Loader/></div>
                </div>
            );
        }
        const orgUsers = OrganisationStore.model && OrganisationStore.model.users;
        const ownerUsers = changeRequest && this.getApprovals(orgUsers, changeRequest.approvals.map(v => v.user));
        const user = orgUsers.find(v => v.id === changeRequest.user);
        return (
            <div
              style={{ opacity: ChangeRequestStore.isLoading ? 0.5 : 1 }} data-test="change-requests-page" id="change-requests-page"
              className="app-container container-fluid"
            >
                <div className="row">
                    <Flex className="mb-2">
                        <h3 className="ml-0">
                            {changeRequest.title}
                        </h3>
                        <div className="list-item-footer faint">
                            Created at {moment(changeRequest.created_date).format('Do MMM YYYY HH:mma')} by {changeRequest.user && user.first_name} {user && user.last_name}
                        </div>
                    </Flex>
                    <div className="ml-4" style={{ width: 330 }}>
                        <InputGroup component={(
                            <div>
                                <Row>
                                    <Button className="btn--link" onClick={() => this.setState({ showUsers: true })}>Assignees <span className="ml-2 icon ion-md-cog"/> </Button>
                                </Row>
                                <Row className="mt-2">
                                    {ownerUsers && ownerUsers.map(u => (
                                        <Row onClick={() => this.removeOwner(u.id)} className="chip chip--active">
                                            <span className="font-weight-bold">
                                                {u.first_name} {u.last_name}
                                            </span>
                                            <span className="chip-icon ion ion-ios-close"/>
                                        </Row>
                                    ))}
                                </Row>
                                <UserSelect
                                  users={orgUsers}
                                  value={ownerUsers && ownerUsers.map(v => v.id)}
                                  onAdd={this.addOwner}
                                  onRemove={this.removeOwner}
                                  isOpen={this.state.showUsers} onToggle={() => this.setState({ showUsers: !this.state.showUsers })}
                                />
                            </div>
                        )}
                        />
                    </div>
                </div>


                <Row className="row">
                    <Flex>
                        <Tabs value={this.state.tab} onChange={tab => this.setState({ tab })}>
                            <TabItem data-test="value" tabLabel="New Value" />
                            <TabItem data-test="value" tabLabel="Live Value" />
                        </Tabs>
                        <Row>
                            <div style={{ minHeight: 300 }}/>
                            <Button onClick={this.deleteChangeRequest} className="btn btn-danger">Delete Change Request</Button>
                        </Row>
                    </Flex>

                </Row>

            </div>
        );
    }
};

ChangeRequestsPage.propTypes = {};

module.exports = hot(module)(ConfigProvider(ChangeRequestsPage));
