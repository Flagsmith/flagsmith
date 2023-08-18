import React, { Component } from 'react'
import CreateProjectModal from 'components/modals/CreateProject'
import CreateOrganisationModal from 'components/modals/CreateOrganisation'
import Permission from 'common/providers/Permission'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'

const ProjectSelectPage = class extends Component {
  static displayName = 'ProjectSelectPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {}
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.PROJECT_SELECT)
    const { state } = this.props.location
    if (state && state.create) {
      this.newProject()
    }
  }

  newProject = () => {
    openModal(
      'Create Project',
      <CreateProjectModal
        onSave={({ environmentId, projectId }) => {
          this.context.router.history.push(
            `/project/${projectId}/environment/${environmentId}/features?new=true`,
          )
        }}
      />,
      'p-0 side-modal',
    )
  }

  newOrganisation = () => {
    openModal('Create Organisation', <CreateOrganisationModal />, 'side-modal')
  }

  render() {
    const isAdmin = AccountStore.isAdmin()
    return (
      <div
        data-test='project-select-page'
        id='project-select-page'
        className='app-container container'
      >
        <PageTitle title={'Your projects'}>
          Projects let you create and manage a set of features and configure
          them between multiple app environments.
        </PageTitle>
        <Panel title='Organisation' className='no-pad'>
          <Row space>
            <AccountProvider>
              {({ organisation }) =>
                organisation && (
                  <OrganisationSelect
                    onChange={(organisationId) => {
                      AppActions.selectOrganisation(organisationId)
                      AppActions.getOrganisation(organisationId)
                    }}
                  />
                )
              }
            </AccountProvider>
            {!Utils.getFlagsmithHasFeature('disable_create_org') &&
              (!Project.superUserCreateOnly ||
                (Project.superUserCreateOnly &&
                  AccountStore.model.is_superuser)) && (
                <div className='pl-3 pr-3 mb-2'>
                  <Flex className='text-center'>
                    <Button onClick={this.newOrganisation}>
                      Create Organisation
                    </Button>
                  </Flex>
                </div>
              )}
          </Row>
        </Panel>
        <hr className='py-0 my-5' />
        <OrganisationProvider>
          {({ isLoading, projects }) => (
            <div>
              {projects && projects.length ? (
                <div className='flex-row pl-0 pr-0'></div>
              ) : isAdmin ? (
                <div className='container-mw-700 mb-4'>
                  <h5 className='mb-2'>
                    Great! Now you can create your first project.
                  </h5>
                  <p className='fs-small lh-sm mb-0'>
                    When you create a project we'll also generate a{' '}
                    <strong>development</strong> and <strong>production</strong>{' '}
                    environment for you.
                  </p>
                  <p className='fs-small lh-sm mb-0'>
                    You can create features for your project, then enable and
                    configure them per environment.
                  </p>
                </div>
              ) : (
                <div className='container-mw-700 mb-4'>
                  <p className='fs-small lh-sm mb-0'>
                    You do not have access to any projects within this
                    Organisation. If this is unexpected please contact a member
                    of the Project who has Administrator privileges. Users can
                    be added to Projects from the Project settings menu.
                  </p>
                </div>
              )}
              {(isLoading || !projects) && (
                <div className='centered-container'>
                  <Loader />
                </div>
              )}
              {!isLoading && (
                <div>
                  <FormGroup>
                    <PanelSearch
                      id='projects-list'
                      className='no-pad panel-projects'
                      listClassName='row mt-2 gy-4'
                      title='Projects'
                      items={projects}
                      renderRow={({ environments, id, name }, i) => {
                        return (
                          <>
                            {i === 0 && (
                              <div className='col-md-6 col-xl-3'>
                                <Permission
                                  level='organisation'
                                  permission='CREATE_PROJECT'
                                  id={AccountStore.getOrganisation().id}
                                >
                                  {({ permission }) => {
                                    return Utils.renderWithPermission(
                                      permission,
                                      Constants.environmentPermissions(
                                        'Create Project',
                                      ),
                                      <Button
                                        disabled={!permission}
                                        onClick={this.newProject}
                                        className='btn-project btn-project-create'
                                      >
                                        <Row className='flex-nowrap'>
                                          <div className='btn-project-icon'>
                                            <Icon
                                              name='plus'
                                              width={32}
                                              fill='#9DA4AE'
                                            />
                                          </div>
                                          <div className='font-weight-medium btn-project-title'>
                                            Create Project
                                          </div>
                                        </Row>
                                      </Button>,
                                    )
                                  }}
                                </Permission>
                              </div>
                            )}
                            <Link
                              key={id}
                              id={`project-select-${i}`}
                              to={`/project/${id}/environment/${
                                environments && environments[0]
                                  ? `${environments[0].api_key}/features`
                                  : 'create'
                              }`}
                              className='clickable col-md-6 col-xl-3'
                              style={{ minWidth: '190px' }}
                            >
                              <Button className='btn-project'>
                                <Row className='flex-nowrap'>
                                  <h2
                                    style={{
                                      backgroundColor:
                                        Utils.getProjectColour(i),
                                    }}
                                    className='btn-project-letter mb-0'
                                  >
                                    {name[0]}
                                  </h2>
                                  <div className='font-weight-medium btn-project-title'>
                                    {name}
                                  </div>
                                </Row>
                              </Button>
                            </Link>
                          </>
                        )
                      }}
                      renderNoResults={
                        <div>
                          <Permission
                            level='organisation'
                            permission='CREATE_PROJECT'
                            id={AccountStore.getOrganisation().id}
                          >
                            {({ permission }) => {
                              return Utils.renderWithPermission(
                                permission,
                                Constants.environmentPermissions(
                                  'Create Project',
                                ),
                                <div className='col-md-6 col-xl-3'>
                                  <Button
                                    disabled={!permission}
                                    onClick={this.newProject}
                                    data-test='create-first-project-btn'
                                    id='create-first-project-btn'
                                    className='btn-project btn-project-create'
                                  >
                                    <Row>
                                      <div className='btn-project-icon'>
                                        <Icon
                                          name='plus'
                                          width={32}
                                          fill='#9DA4AE'
                                        />
                                      </div>
                                      <div className='font-weight-medium'>
                                        Create Project
                                      </div>
                                    </Row>
                                  </Button>
                                </div>,
                              )
                            }}
                          </Permission>
                        </div>
                      }
                      filterRow={(item, search) =>
                        item.name.toLowerCase().indexOf(search) > -1
                      }
                      sorting={[
                        {
                          default: true,
                          label: 'Name',
                          order: 'asc',
                          value: 'name',
                        },
                      ]}
                    />
                  </FormGroup>
                </div>
              )}
            </div>
          )}
        </OrganisationProvider>
      </div>
    )
  }
}

ProjectSelectPage.propTypes = {}

module.exports = ConfigProvider(ProjectSelectPage)
