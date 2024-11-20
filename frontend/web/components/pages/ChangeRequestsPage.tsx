import { FC, useEffect, useState } from 'react'
import FeatureListStore from 'common/stores/feature-list-store'
import OrganisationStore from 'common/stores/organisation-store'
import { RouterChildContext } from 'react-router'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import ProjectStore from 'common/stores/project-store'
import { ChangeRequestSummary, Environment, User } from 'common/types/responses'
import Utils from 'common/utils/utils'
import { Link } from 'react-router-dom'
import { IonIcon } from '@ionic/react'
import { timeOutline } from 'ionicons/icons'
import PageTitle from 'components/PageTitle'
import PlanBasedAccess, {
  featureDescriptions,
} from 'components/PlanBasedAccess'
import InfoMessage from 'components/InfoMessage'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import PanelSearch from 'components/PanelSearch'
import JSONReference from 'components/JSONReference'
import ChangeRequestPage from './ChangeRequestPage'
import moment from 'moment'
import Icon from 'components/Icon'

type ChangeRequestsPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
      id: string
    }
  }
}

const ChangeRequestsPage: FC<ChangeRequestsPageType> = ({ match, router }) => {
  const { environmentId, id, projectId } = match.params
  const [page, setPage] = useState(1)
  const [pageCommitted, setPageCommitted] = useState(1)

  const [live_after, setLive_after] = useState(new Date().toISOString())
  const [showArchived, setShowArchived] = useState(false)
  const [_, setUpdate] = useState(Date.now())
  const organisationId = AccountStore.getOrganisation()?.id
  const environment = ProjectStore.getEnvironment(
    environmentId,
  ) as unknown as Environment

  // @ts-ignore
  const organisation = OrganisationStore.model as any
  const users = organisation?.users as User[]
  const { data: committed, isLoading: committedLoading } =
    useGetChangeRequestsQuery({
      committed: true,
      environmentId,
      page: pageCommitted,
      page_size: 50,
    })

  const { data: changeRequests, isLoading } = useGetChangeRequestsQuery({
    environmentId,
    page,
    page_size: 50,
  })

  useEffect(() => {
    AppActions.getOrganisation(organisationId)
  }, [organisationId])

  useEffect(() => {
    const forceUpdate = () => {
      setUpdate(Date.now())
    }
    OrganisationStore.on('change', forceUpdate)

    return () => {
      OrganisationStore.off('change', forceUpdate)
    }
  }, [])

  return (
    <div
      data-test='change-requests-page'
      id='change-requests-page'
      className='app-container container'
    >
      {!!Utils.getPlansPermission('4_EYES') && (
        <PageTitle title={featureDescriptions['4_EYES'].title}>
          {featureDescriptions['4_EYES'].description}
        </PageTitle>
      )}
      <PlanBasedAccess feature={'4_EYES'} theme={'page'}>
        <Flex>
          <div>
            <p>
              {environment &&
              !Utils.changeRequestsEnabled(
                environment.minimum_change_request_approvals,
              ) ? (
                <InfoMessage>
                  To enable this feature set a minimum number of approvals in{' '}
                  <Link
                    to={`/project/${projectId}/environment/${environmentId}/settings`}
                  >
                    Environment Settings
                  </Link>
                </InfoMessage>
              ) : null}
            </p>
            <Tabs urlParam={'tab'}>
              <TabItem
                tabLabelString='Open'
                tabLabel={
                  <span className='flex-row justify-content-center'>
                    Open
                    {changeRequests?.count && (
                      <div className='counter-value ml-1'>
                        {changeRequests.count}
                      </div>
                    )}
                  </span>
                }
              >
                <PanelSearch
                  renderSearchWithNoResults
                  id='users-list'
                  title='Change Requests'
                  className='mt-4 no-pad'
                  isLoading={isLoading || !changeRequests || !organisation}
                  items={changeRequests?.results}
                  paging={changeRequests}
                  nextPage={() => setPage(page + 1)}
                  prevPage={() => setPage(page + 1)}
                  goToPage={setPage}
                  renderFooter={() => (
                    <JSONReference
                      className='mt-4 ml-3'
                      title={'Change Requests'}
                      json={changeRequests?.results}
                    />
                  )}
                  renderRow={({
                    created_at,
                    description,
                    id,
                    live_from,
                    title,
                    user: _user,
                  }: ChangeRequestSummary) => {
                    const user = users?.find((v) => v.id === _user)
                    const isScheduled =
                      new Date(`${live_from}`).valueOf() > new Date().valueOf()
                    return (
                      <Link
                        to={`/project/${projectId}/environment/${environmentId}/change-requests/${id}`}
                        className='flex-row list-item clickable'
                      >
                        <Flex className='table-column px-3'>
                          <div className='font-weight-medium'>
                            {title}
                            {isScheduled && (
                              <span className='ml-1 mr-4 ion'>
                                <IonIcon icon={timeOutline} />
                              </span>
                            )}
                          </div>
                          <div className='list-item-subtitle mt-1'>
                            Created{' '}
                            {moment(created_at).format('Do MMM YYYY HH:mma')} by{' '}
                            {(user && user.first_name) || 'Unknown'}{' '}
                            {(user && user.last_name) || 'user'}
                            {description ? ` - ${description}` : ''}
                          </div>
                        </Flex>
                        <div className='table-column'>
                          <Icon
                            name='chevron-right'
                            fill='#9DA4AE'
                            width={20}
                          />
                        </div>
                      </Link>
                    )
                  }}
                />
              </TabItem>
              <TabItem
                tabLabelString='Closed'
                tabLabel={
                  <span className='flex-row justify-content-center'>
                    Closed
                  </span>
                }
              >
                <PanelSearch
                  renderSearchWithNoResults
                  id='users-list'
                  title='Change Requests'
                  className='mt-4 no-pad'
                  isLoading={
                    committedLoading || !committed?.results || !organisation
                  }
                  items={committed?.results}
                  paging={committed}
                  nextPage={() => setPageCommitted(pageCommitted + 1)}
                  prevPage={() => setPageCommitted(pageCommitted - 1)}
                  goToPage={setPageCommitted}
                  renderFooter={() => (
                    <JSONReference
                      className='mt-4 ml-3'
                      title={'Change Requests'}
                      json={committed?.results}
                    />
                  )}
                  renderRow={({
                    created_at,
                    id,
                    title,
                    user: _user,
                  }: ChangeRequestSummary) => {
                    const user = users?.find((v) => v.id === _user)
                    return (
                      <Link
                        to={`/project/${projectId}/environment/${environmentId}/change-requests/${id}`}
                        className='flex-row list-item clickable'
                      >
                        <Flex className='table-column px-3'>
                          <div className='font-weight-medium'>{title}</div>
                          <div className='list-item-subtitle mt-1'>
                            Live from{' '}
                            {moment(created_at).format('Do MMM YYYY HH:mma')} by{' '}
                            {(user && user.first_name) || 'Unknown'}{' '}
                            {(user && user.last_name) || 'user'}
                          </div>
                        </Flex>
                        <div className='table-column'>
                          <Icon
                            name='chevron-right'
                            fill='#9DA4AE'
                            width={20}
                          />
                        </div>
                      </Link>
                    )
                  }}
                />
              </TabItem>
            </Tabs>
          </div>
        </Flex>
      </PlanBasedAccess>
    </div>
  )
}

export default ChangeRequestsPage
