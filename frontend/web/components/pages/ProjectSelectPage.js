import React, { Component } from 'react';
import CreateProjectModal from '../modals/CreateProject';

const ProjectSelectPage = class extends Component {
    static displayName = 'ProjectSelectPage';

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {};
        AppActions.getOrganisation(AccountStore.getOrganisation().id);
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.PROJECT_SELECT);
        const { state } = this.props.location;
        if (state && state.create) {
            this.newProject();
        }
    };

    newProject = () => {
        openModal('Create  Project', <CreateProjectModal onSave={({ projectId, environmentId }) => {
            this.context.router.history.push(`/project/${projectId}/environment/${environmentId}/features?new=true`);
        }}
        />);
    };

    render() {
        const isAdmin = AccountStore.isAdmin();
        return (
            <div data-test="project-select-page" id="project-select-page" className="app-container container pt-5">
                <OrganisationProvider>
                    {({ isLoading, name, projects, users }) => (
                        <div>
                            {projects && projects.length ? (
                                <div className="flex-row pl-0 pr-0">
                                    <div className="col-md-9 pl-0 pr-0">
                                        <h3>Your projects</h3>
                                        <p>
                                            Projects let you create and manage a set of features and configure them between
                                            multiple
                                            app environments.
                                        </p>
                                    </div>
                                    <div className="col-md-3 pl-0 pr-0">
                                        <Permission level="organisation" permission="CREATE_PROJECT" id={AccountStore.getOrganisation().id}>
                                            {({ permission, isLoading }) => {
                                                const canCreate = permission || !this.props.hasFeature('organisation_permissions');
                                                return Utils.renderWithPermission(permission, Constants.environmentPermissions('Create Project'), (
                                                    <Button disabled={!canCreate} className="float-right btn__md-full mb-md-0 mb-3" onClick={this.newProject}>
                                                        Create Project
                                                    </Button>
                                                ));
                                            }}
                                        </Permission>
                                    </div>
                                </div>
                            ) : isAdmin ? (
                                <div className="text-center">
                                    <h3>Great! Now you can create your first project.</h3>
                                    <p>
                                        When you create a project we'll also generate a
                                        {' '}
                                        <strong>development</strong>
                                        {' '}
                                        and
                                        {' '}
                                        <strong>production</strong>
                                        {' '}
                                        environment for you.
                                    </p>
                                    <p>
                                        You can create features for your project, then enable and configure them per
                                        environment.
                                    </p>
                                </div>
                            ) : (
                                <div>
                                    <h3>Your projects</h3>
                                    <p>
                                        You do not have access to any projects within this Organisation. If this is unexpected please contact a member of the Project who has Administrator privileges. Users can be added to Projects from the Project settings menu.
                                    </p>
                                </div>
                            )
                            }

                            {(isLoading || !projects) && <div className="centered-container"><Loader/></div>}
                            {!isLoading && (
                                <div className="conatiner">
                                    <FormGroup>
                                        <PanelSearch
                                          id="projects-list"
                                          className="no-pad"
                                          title="Projects"
                                          items={projects}
                                          renderRow={({ id, name, environments }, i) => (
                                              <Link
                                                key={id} className="list-item clickable"
                                                id={`project-select-${i}`}
                                                to={`/project/${id}/environment/${environments && environments[0]
                                                    ? `${environments[0].api_key}/features` : 'create'
                                                }`}
                                              >
                                                  <Row>
                                                      <Flex className="align-start">
                                                          <ButtonLink>
                                                              {name}
                                                          </ButtonLink>
                                                      </Flex>
                                                      <span className="text__link icon ion-ios-arrow-forward list-item"/>
                                                  </Row>
                                              </Link>
                                          )}
                                          renderNoResults={(
                                              <div className="text-center">
                                                  <div className="text-center">
                                                      <div>
                                                          <Permission level="organisation" permission="CREATE_PROJECT" id={AccountStore.getOrganisation().id}>
                                                              {({ permission, isLoading }) => {
                                                                  const canCreate = permission || !this.props.hasFeature('organisation_permissions');
                                                                  return Utils.renderWithPermission(permission, Constants.environmentPermissions('Create Project'), (
                                                                      <button
                                                                        disabled={!canCreate}
                                                                        onClick={this.newProject}
                                                                        className="btn btn-primary btn-lg"
                                                                        data-test="create-first-project-btn"
                                                                        id="create-first-project-btn"
                                                                      >
                                                                          <span className="icon ion-ios-rocket"/>
                                                                          {' '}
                                                                          Create a project
                                                                      </button>
                                                                  ));
                                                              }}
                                                          </Permission>

                                                      </div>
                                                  </div>
                                              </div>
                                            )}
                                          filterRow={(item, search) => item.name.toLowerCase().indexOf(search) > -1}
                                        />
                                    </FormGroup>

                                </div>
                            )}
                        </div>
                    )}
                </OrganisationProvider>
            </div>
        );
    }
};

ProjectSelectPage.propTypes = {};

module.exports = ConfigProvider(ProjectSelectPage);
