import React, { FC, useCallback } from 'react'
import Button from 'components/base/forms/Button'
import AccountProvider from 'common/providers/AccountProvider'
import CreateOrganisationModal from 'components/modals/CreateOrganisation'
import { Organisation, User } from 'common/types/responses'
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import PanelSearch from 'components/PanelSearch'
import AppActions from 'common/dispatcher/app-actions'
import { useHistory } from 'react-router-dom'
import ConfigProvider from 'common/providers/ConfigProvider'

const OrganisationsPage: FC = () => {
  const history = useHistory()

  const handleCreateOrganisationClick = useCallback(() => {
    openModal('Create Organisation', <CreateOrganisationModal />, 'side-modal')
  }, [])

  const onSave = (id: number) => {
    AppActions.selectOrganisation(id)
    AppActions.getOrganisation(id)
    history.push(Utils.getOrganisationHomePage(id))
  }
  return (
    <AccountProvider onSave={onSave}>
      {({ user }: { user: User & { organisations: Organisation[] } }) => {
        return (
          <div className='app-container container'>
            <PanelSearch
              id='organisation-list'
              className='no-pad panel-projects'
              listClassName='row mt-n2 gy-3'
              title='Organisations'
              filterRow={(item: Organisation, search: string) =>
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
              header={
                <div className='fs-small mb-2 lh-sm'>
                  Organisations allow you to manage multiple projects within a
                  team.
                </div>
              }
              items={(user?.organisations || []) as Organisation[]}
              renderRow={({ id, name }, i) => {
                return (
                  <>
                    {i === 0 && (
                      <div className='col-md-6 col-xl-3'>
                        {Utils.canCreateOrganisation() && (
                          <Button
                            data-test='create-organisation-btn'
                            onClick={handleCreateOrganisationClick}
                            className='btn-project btn-project-create'
                          >
                            <Row className='flex-nowrap'>
                              <div className='btn-project-icon'>
                                <Icon name='plus' width={32} fill='#9DA4AE' />
                              </div>
                              <div className='font-weight-medium btn-project-title'>
                                Create Organisation
                              </div>
                            </Row>
                          </Button>
                        )}
                      </div>
                    )}
                    <a
                      key={id}
                      id={`organisation-select-${i}`}
                      onClick={() => {
                        AppActions.selectOrganisation(id)
                        AppActions.getOrganisation(id)
                        history.push(Utils.getOrganisationHomePage())
                      }}
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
                    </a>
                  </>
                )
              }}
            />
          </div>
        )
      }}
    </AccountProvider>
  )
}

export default ConfigProvider(OrganisationsPage)
