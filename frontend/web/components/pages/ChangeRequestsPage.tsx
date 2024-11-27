import { FC, ReactNode, useEffect, useState } from 'react'
import OrganisationStore from 'common/stores/organisation-store'
import { RouterChildContext } from 'react-router'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import ProjectStore from 'common/stores/project-store'
import {
  ChangeRequest,
  ChangeRequestSummary,
  Environment,
  PagedResponse,
  User,
} from 'common/types/responses'
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
import moment from 'moment'
import Icon from 'components/Icon'
import v from 'refractor/lang/v'
import ConfigProvider from 'common/providers/ConfigProvider'

type ChangeRequestsPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const ChangeRequestsPage: FC<ChangeRequestsPageType> = ({ match, router }) => {
  const { environmentId, projectId } = match.params
  const [page, setPage] = useState(1)
  const [pageCommitted, setPageCommitted] = useState(1)
  const organisationId = AccountStore.getOrganisation()?.id
  const environment = ProjectStore.getEnvironment(
    environmentId,
  ) as unknown as Environment

  // @ts-ignore

  const { data: committed, isLoading: committedLoading } =
    useGetChangeRequestsQuery(
      {
        committed: true,
        environmentId,
        page: pageCommitted,
        page_size: 10,
      },
      { refetchOnMountOrArgChange: true },
    )

  const { data: changeRequests, isLoading } = useGetChangeRequestsQuery(
    {
      committed: false,
      environmentId,
      page,
      page_size: 10,
    },
    { refetchOnMountOrArgChange: true },
  )

  useEffect(() => {
    AppActions.getOrganisation(organisationId)
  }, [organisationId])

  return (
    <ChangeRequestsInner
      feature={'4_EYES'}
      committedChangeRequests={committed}
      pageCommitted={pageCommitted}
      isLoading={isLoading}
      setPageCommitted={setPageCommitted}
      page={page}
      getLink={(id) =>
        `/project/${projectId}/environment/${environmentId}/change-requests/${id}`
      }
      setPage={setPage}
      changeRequests={changeRequests}
      changeRequestsDisabled={
        environment &&
        !Utils.changeRequestsEnabled(
          environment.minimum_change_request_approvals,
        )
      }
      ChangeRequestsDisabledMessage={
        <InfoMessage>
          To enable this feature set a minimum number of approvals in{' '}
          <Link
            to={`/project/${projectId}/environment/${environmentId}/settings`}
          >
            Environment Settings
          </Link>
        </InfoMessage>
      }
    />
  )
}

type ChangeRequestsInnerType = {
  ChangeRequestsDisabledMessage: ReactNode
  changeRequests: PagedResponse<ChangeRequestSummary> | undefined
  changeRequestsDisabled: boolean
  committedChangeRequests: PagedResponse<ChangeRequestSummary> | undefined
  pageCommitted: number
  feature: '4_EYES' | '4_EYES_PROJECT'
  getLink: (id: string) => string
  isLoading: boolean
  page: number
  setPageCommitted: (page: number) => void
  setPage: (page: number) => void
}

export const ChangeRequestsInner: FC<ChangeRequestsInnerType> = ({
  ChangeRequestsDisabledMessage,
  changeRequests,
  changeRequestsDisabled,
  committedChangeRequests,
  feature,
  getLink,
  isLoading,
  page,
  pageCommitted,
  setPage,
  setPageCommitted,
}) => {
  const [_, setUpdate] = useState(Date.now())

  // @ts-ignore
  const organisation = OrganisationStore.model as any
  const users = organisation?.users as User[]
  useEffect(() => {
    const forceUpdate = () => {
      setUpdate(Date.now())
    }
    OrganisationStore.on('change', forceUpdate)

    return () => {
      OrganisationStore.off('change', forceUpdate)
    }
  }, [])

  const renderItems = (
    items: PagedResponse<ChangeRequestSummary> | undefined,
    page: number,
    setPage: (page: number) => void,
  ) => {
    return (
      <PanelSearch
        renderSearchWithNoResults
        className='mt-4 no-pad'
        isLoading={isLoading || !changeRequests}
        items={items?.results}
        paging={items}
        nextPage={() => setPage(page + 1)}
        prevPage={() => setPage(page + 1)}
        goToPage={setPage}
        renderFooter={() => (
          <JSONReference
            className='mt-4 ml-3'
            title={'Change Requests'}
            json={items?.results}
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
              to={getLink(`${id}`)}
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
                  Created {moment(created_at).format('Do MMM YYYY HH:mma')}
                  {!!user && (
                    <>
                      {' '}
                      by {(user && user.first_name) || 'Unknown'}{' '}
                      {(user && user.last_name) || 'user'}
                    </>
                  )}
                  {description ? ` - ${description}` : ''}
                </div>
              </Flex>
              <div className='table-column'>
                <Icon name='chevron-right' fill='#9DA4AE' width={20} />
              </div>
            </Link>
          )
        }}
      />
    )
  }

  return (
    <div
      data-test='change-requests-page'
      id='change-requests-page'
      className='app-container container'
    >
      {!!Utils.getPlansPermission(feature) && (
        <PageTitle title={featureDescriptions[feature].title}>
          {featureDescriptions[feature].description}
        </PageTitle>
      )}
      <PlanBasedAccess feature={feature} theme={'page'}>
        <Flex>
          <div>
            {changeRequestsDisabled && <p>{ChangeRequestsDisabledMessage}</p>}

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
                {renderItems(changeRequests, page, setPage)}
              </TabItem>
              <TabItem
                tabLabelString='Closed'
                tabLabel={
                  <span className='flex-row justify-content-center'>
                    Closed
                  </span>
                }
              >
                {renderItems(
                  committedChangeRequests,
                  pageCommitted,
                  setPageCommitted,
                )}
              </TabItem>
            </Tabs>
          </div>
        </Flex>
      </PlanBasedAccess>
    </div>
  )
}

export default ConfigProvider(ChangeRequestsPage)
