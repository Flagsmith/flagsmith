import React, { FC, useCallback } from 'react'
import Button from 'components/base/forms/Button'
import AccountProvider from 'common/providers/AccountProvider'
import CreateOrganisationModal from 'components/modals/CreateOrganisation'
import { Organisation } from 'common/types/responses';
import Utils from 'common/utils/utils';
import Constants from 'common/constants';
import AccountStore from 'common/stores/account-store';
import Icon from 'components/Icon';
import Project from 'common/project'
import { Link } from 'react-router-dom';
type OrganisationsPageType = {}

const OrganisationsPage: FC<OrganisationsPageType> = ({}) => {
  const handleCreateOrganisationClick = useCallback(() => {
    openModal('Create Organisation', <CreateOrganisationModal />, 'side-modal')
  }, [])

  return (
    <AccountProvider>
      {({ user }) => {
        return (
          <div className='app-container container'>
            <div className='d-flex justify-content-between'>
              <h5>Organisations</h5>
              {!Utils.getFlagsmithHasFeature('disable_create_org') &&
                  (!Project.superUserCreateOnly ||
                      (Project.superUserCreateOnly && AccountStore.isSuper())) && (
                      <Button onClick={handleCreateOrganisationClick}>
                Create New Organisation
              </Button>
                  )
              }
            </div>


            <PanelSearch
                id='projects-list'
                className='no-pad panel-projects'
                listClassName='row mt-n2 gy-4'
                title='Organisations'
                header={
                  <div className='fs-small mb-2 lh-sm'>
                    Organisations allow you to manage multiple projects within a team.
                  </div>
                }
                items={user?.organisations||[]}
                renderRow={(
                    { id, name }: Organisation,
                    i: number,
                ) => {
                  return (
                      <>
                        {i === 0 && (
                            <div className='col-md-6 col-xl-3'>
                              {!Utils.getFlagsmithHasFeature('disable_create_org') &&
                                  (!Project.superUserCreateOnly ||
                                      (Project.superUserCreateOnly && AccountStore.isSuper())) && (
                                  <Button
                                      onClick={handleCreateOrganisationClick}
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
                                        Create Organisation
                                      </div>
                                    </Row>
                                  </Button>
                                  )}
                              )}
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
                              <div className='font-weight-medium btn-project-title overflow-hidden'>
                                {name}
                              </div>
                            </Row>
                          </Button>
                        </Link>
                      </>
                  )
                }}

          </div>
        )
      }}
    </AccountProvider>
  )
}

export default OrganisationsPage
