import React, { Component } from 'react';
import ChangeRequestStore from '../../../common/stores/change-requests-store';
import OrganisationStore from '../../../common/stores/organisation-store';
import ProjectStore from '../../../common/stores/project-store';
import PaymentModal from '../modals/Payment';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';

const ChangeRequestsPage = class extends Component {
    static displayName = 'ChangeRequestsPage';

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {
            tags: [],
            showArchived: false,
            live_after: new Date().toISOString(),
        };
        ES6Component(this);
        this.listenTo(ChangeRequestStore, 'change', () => this.forceUpdate());
        this.listenTo(OrganisationStore, 'change', () => this.forceUpdate());
    }


    componentWillUpdate() {

    }

    componentDidMount = () => {
        AppActions.getChangeRequests(this.props.match.params.environmentId, {});
        AppActions.getChangeRequests(this.props.match.params.environmentId, { committed: true });
        AppActions.getChangeRequests(this.props.match.params.environmentId, { live_from_after: this.state.live_after });
        AppActions.getOrganisation(AccountStore.getOrganisation().id);
    };

    render() {
        const { projectId, environmentId, envId } = this.props.match.params;
        const readOnly = this.props.hasFeature('read_only_mode');
        const data = ChangeRequestStore.model && ChangeRequestStore.model[environmentId] && ChangeRequestStore.model[environmentId] && ChangeRequestStore.model[environmentId].results;
        const dataPaging = ChangeRequestStore.model && ChangeRequestStore.model[environmentId] && ChangeRequestStore.model[environmentId] && ChangeRequestStore.model[environmentId];

        const dataClosed = ChangeRequestStore.committed && ChangeRequestStore.committed[environmentId] && ChangeRequestStore.committed[environmentId].results;
        const dataClosedPaging = ChangeRequestStore.committed && ChangeRequestStore.committed[environmentId] && ChangeRequestStore.committed[environmentId];

        const dataScheduled = ChangeRequestStore.scheduled && ChangeRequestStore.scheduled[environmentId] && ChangeRequestStore.scheduled[environmentId].results;
        const dataScheduledPaging = ChangeRequestStore.scheduled && ChangeRequestStore.scheduled[environmentId] && ChangeRequestStore.scheduled[environmentId];

        const hasPermission = Utils.getPlansPermission('4_EYES');
        const environment = ProjectStore.getEnvironment(environmentId);
        return (
            <div data-test="change-requests-page" id="change-requests-page" className="app-container container">
                <Flex>
                    <h3>Change Requests</h3>
                    {!hasPermission && (
                        <p>
                            View and manage your feature changes with a Change Request flow with our <a
                              href="#" onClick={() => {
                                  openModal('Payment plans', <PaymentModal
                                    viewOnly={false}
                                  />, null, { large: true });
                              }}
                            >Scaleup plan
                            </a>. Find out more <a href="https://docs.flagsmith.com/advanced-use/change-requests" target="_blank">here</a>.
                        </p>
                    )}
                    {hasPermission && (
                        <p>
                            {environment && !environment.minimum_change_request_approvals ? (
                                <span>
                                    To enable this feature set a minimum number of approvals in <Link to={`/project/${projectId}/environment/${environmentId}/settings`}>Environment Settings</Link>
                                </span>
                            ) : (
                                <div>
                                    View and manage requests to change feature flags with <ButtonLink
                                      href="https://docs.flagsmith.com/advanced-use/change-requests"
                                      target="_blank"
                                    >Change Requests</ButtonLink>.
                                </div>

                            )}
                        </p>
                    )}

                    <Tabs
                      value={this.state.tab}
                      onChange={(tab) => {
                          this.setState({ tab });
                      }}
                    >
                        <TabItem tabLabel={`Open${data ? ` (${dataPaging.count})` : ''}`}>
                            <PanelSearch
                              renderSearchWithNoResults
                              id="users-list"
                              title="Change Requests"
                              className="mt-4 mx-2"
                              isLoading={ChangeRequestStore.isLoading || !data || !OrganisationStore.model}
                              icon="ion-md-git-pull-request"
                              items={data}
                              paging={dataPaging}
                              nextPage={() => AppActions.getChangeRequests(this.props.match.params.environmentId, {}, dataPaging.next)}
                              prevPage={() => AppActions.getChangeRequests(this.props.match.params.environmentId, {}, dataPaging.previous)}
                              goToPage={page => AppActions.getChangeRequests(this.props.match.params.environmentId, {}, `${Project.api}environments/${environmentId}/list-change-requests/?page=${page}`)}
                              renderRow={({ title, user: _user, created_at, id }, index) => {
                                  const user = (OrganisationStore.model && OrganisationStore.model.users && OrganisationStore.model.users.find(v => v.id === _user)) || {};
                                  return (
                                      <Link to={`/project/${projectId}/environment/${environmentId}/change-requests/${id}`}>
                                          <Row className="list-item clickable">
                                              <span className="ion text-primary mr-4 icon ion-md-git-pull-request"/>
                                              <div>
                                                  <ButtonLink>
                                                      {title}
                                                  </ButtonLink>
                                                  <div className="list-item-footer faint">
                                                       Created at {moment(created_at).format('Do MMM YYYY HH:mma')} by {user && user.first_name} {user && user.last_name}
                                                  </div>
                                              </div>
                                          </Row>
                                      </Link>
                                  );
                              }}
                            />
                        </TabItem>
                        {this.props.hasFeature('scheduling') && (
                        <TabItem tabLabel={`Scheduled${dataScheduledPaging ? ` (${dataScheduledPaging.count})` : ''}`}>
                            <PanelSearch
                              renderSearchWithNoResults
                              id="users-list"
                              title="Change Requests"
                              className="mt-4 mx-2"
                              isLoading={ChangeRequestStore.isLoading || !dataScheduled || !OrganisationStore.model}
                              icon="ion-md-git-pull-request"
                              items={dataScheduled}
                              paging={dataScheduledPaging}
                              nextPage={() => AppActions.getChangeRequests(this.props.match.params.environmentId, { live_from_after: this.state.live_after }, dataPaging.next)}
                              prevPage={() => AppActions.getChangeRequests(this.props.match.params.environmentId, { live_from_after: this.state.live_after }, dataPaging.previous)}
                              goToPage={page => AppActions.getChangeRequests(this.props.match.params.environmentId, { live_from_after: this.state.live_after }, `${Project.api}environments/${environmentId}/list-change-requests/?page=${page}`)}

                              renderRow={({ title, user: _user, created_at, id }, index) => {
                                  const user = OrganisationStore.model && OrganisationStore.model.users.find(v => v.id === _user);
                                  return (
                                      <Link to={`/project/${projectId}/environment/${environmentId}/change-requests/${id}`}>
                                          <Row className="list-item clickable">
                                              <span className="ion text-primary mr-4 icon ion-md-git-pull-request"/>
                                              <div>
                                                  <ButtonLink>
                                                      {title}
                                                  </ButtonLink>
                                                  <div className="list-item-footer faint">
                                                            Created at {moment(created_at).format('Do MMM YYYY HH:mma')} by {user && user.first_name} {user && user.last_name}
                                                  </div>
                                              </div>
                                          </Row>
                                      </Link>
                                  );
                              }}
                            />
                        </TabItem>
                        )}
                        <TabItem tabLabel={`Closed${dataClosedPaging ? ` (${dataClosedPaging.count})` : ''}`}>
                            <PanelSearch
                              renderSearchWithNoResults
                              id="users-list"
                              title="Change Requests"
                              className="mt-4 mx-2"
                              isLoading={ChangeRequestStore.isLoading || !data || !OrganisationStore.model}
                              icon="ion-md-git-pull-request"
                              items={dataClosed}
                              paging={dataClosedPaging}
                              nextPage={() => AppActions.getChangeRequests(this.props.match.params.environmentId, { committed: true }, dataPaging.next)}
                              prevPage={() => AppActions.getChangeRequests(this.props.match.params.environmentId, { committed: true }, dataPaging.previous)}
                              goToPage={page => AppActions.getChangeRequests(this.props.match.params.environmentId, { committed: true }, `${Project.api}environments/${environmentId}/list-change-requests/?page=${page}`)}

                              renderRow={({ title, user: _user, created_at, id }, index) => {
                                  const user = OrganisationStore.model && OrganisationStore.model.users.find(v => v.id === _user);
                                  return (
                                      <Link to={`/project/${projectId}/environment/${environmentId}/change-requests/${id}`}>
                                          <Row className="list-item clickable">
                                              <span className="ion text-primary mr-4 icon ion-md-git-pull-request"/>
                                              <div>
                                                  <ButtonLink>
                                                      {title}
                                                  </ButtonLink>
                                                  <div className="list-item-footer faint">
                                                       Created at {moment(created_at).format('Do MMM YYYY HH:mma')} by {user && user.first_name} {user && user.last_name}
                                                  </div>
                                              </div>
                                          </Row>
                                      </Link>
                                  );
                              }}
                            />
                        </TabItem>
                    </Tabs>
                </Flex>

            </div>
        );
    }
};

ChangeRequestsPage.propTypes = {};

module.exports = hot(module)(ConfigProvider(ChangeRequestsPage));
