import React, { Component } from 'react';
import ChangeRequestStore from '../../../common/stores/change-requests-store';
import OrganisationStore from '../../../common/stores/organisation-store';

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
        };
        ES6Component(this);
        this.listenTo(ChangeRequestStore, 'change', () => this.forceUpdate());
        this.listenTo(OrganisationStore, 'change', () => this.forceUpdate());
        AppActions.getChangeRequests(this.props.match.params.environmentId);
        AppActions.getOrganisation(AccountStore.getOrganisation().id);
    }

    componentWillUpdate() {

    }

    componentDidMount = () => {

    };

    render() {
        const { projectId, environmentId, envId } = this.props.match.params;
        const readOnly = this.props.hasFeature('read_only_mode');
        const data = ChangeRequestStore.model && ChangeRequestStore.model[environmentId];
        return (
            <div data-test="change-requests-page" id="change-requests-page" className="app-container container">
                <Flex>
                    <h3>Change Requests</h3>
                    <p>
                        View and manage requests to change feature flags
                    </p>
                    <PanelSearch
                      renderSearchWithNoResults
                      id="users-list"
                      title="Change Requests"
                      className="no-pad"
                      isLoading={ChangeRequestStore.isLoading || !data || !OrganisationStore.model}
                      icon="ion-md-git-pull-request"
                      items={data}
                      renderRow={({ title, user: _user, created_date, id }, index) => {
                          const user = OrganisationStore.model.users.find(v => v.id === _user);
                          return (
                              <Link to={`/project/${projectId}/environment/${environmentId}/change-requests/${id}`}>
                                  <Row className="list-item clickable">
                                      <span className="ion text-primary mr-4 icon ion-md-git-pull-request"/>
                                      <div>
                                          <ButtonLink>
                                              {title}
                                          </ButtonLink>
                                          <div className="list-item-footer faint">
                                                Created at {moment(created_date).format('Do MMM YYYY HH:mma')} by {user && user.first_name} {user && user.last_name}
                                          </div>
                                      </div>
                                  </Row>
                              </Link>
                          );
                      }}
                    />
                </Flex>

            </div>
        );
    }
};

ChangeRequestsPage.propTypes = {};

module.exports = hot(module)(ConfigProvider(ChangeRequestsPage));
