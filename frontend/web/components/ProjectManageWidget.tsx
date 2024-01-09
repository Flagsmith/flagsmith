import { FC, useCallback, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { RouterChildContext } from 'react-router'

import API from 'project/api'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import AccountStore from 'common/stores/account-store'
import Permission from 'common/providers/Permission'
import ConfigProvider from 'common/providers/ConfigProvider'
import { Project } from 'common/types/responses'
import Button from './base/forms/Button'
import PanelSearch from './PanelSearch'
import Icon from './Icon'

const OrganisationProvider = require('common/providers/OrganisationProvider')
const CreateProjectModal = require('components/modals/CreateProject')

interface OrganisationContext {
  isLoading: boolean
  projects: unknown[]
}

type SegmentsPageType = {
  router: RouterChildContext['router']
}

const ProjectManageWidget: FC<SegmentsPageType> = ({ router }) => {
  const isAdmin = AccountStore.isAdmin()

  const handleCreateProjectClick = useCallback(() => {
    openModal(
      'Create Project',
      <CreateProjectModal
        onSave={({
          environmentId,
          projectId,
        }: {
          environmentId: string
          projectId: string
        }) => {
          router.history.push(
            `/project/${projectId}/environment/${environmentId}/features?new=true`,
          )
        }}
      />,
      'p-0 side-modal',
    )
  }, [router.history])

  useEffect(() => {
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
  }, [])

  useEffect(() => {
    API.trackPage(Constants.pages.PROJECT_SELECT)
    const { state } = router.route.location as { state: { create?: boolean } }
    if (state && state.create) {
      handleCreateProjectClick()
    }
  }, [handleCreateProjectClick, router.route.location])

  return (
    <div data-test='projec-manage-widget' id='projec-manage-widget'>
      <OrganisationProvider>
        {({ isLoading, projects }: OrganisationContext) => (
          <div>
            {(projects && projects.length) || isLoading ? (
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
                  Organisation. If this is unexpected please contact a member of
                  the Project who has Administrator privileges. Users can be
                  added to Projects from the Project settings menu.
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
                    listClassName='row mt-n2 gy-4'
                    title='Your projects'
                    items={projects}
                    renderRow={(
                      { environments, id, name }: Project,
                      i: number,
                    ) => {
                      return (
                        <>
                          {i === 0 && (
                            <div className='col-md-6 col-xl-3'>
                              <Permission
                                level='organisation'
                                permission={Utils.getCreateProjectPermission(
                                  AccountStore.getOrganisation(),
                                )}
                                id={AccountStore.getOrganisation().id}
                              >
                                {({ permission }) => {
                                  return Utils.renderWithPermission(
                                    permission,
                                    Constants.organisationPermissions(
                                      Utils.getCreateProjectPermissionDescription(
                                        AccountStore.getOrganisation(),
                                      ),
                                    ),
                                    <Button
                                      disabled={!permission}
                                      onClick={handleCreateProjectClick}
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
                                    backgroundColor: Utils.getProjectColour(i),
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
                          permission={Utils.getCreateProjectPermission(
                            AccountStore.getOrganisation(),
                          )}
                          id={AccountStore.getOrganisation().id}
                        >
                          {({ permission }) => {
                            return Utils.renderWithPermission(
                              permission,
                              Constants.organisationPermissions(
                                Utils.getCreateProjectPermissionDescription(
                                  AccountStore.getOrganisation(),
                                ),
                              ),
                              <div className='col-md-6 col-xl-3'>
                                <Button
                                  disabled={!permission}
                                  onClick={handleCreateProjectClick}
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
                    filterRow={(item: Project, search: string) =>
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

export default ConfigProvider(ProjectManageWidget)
