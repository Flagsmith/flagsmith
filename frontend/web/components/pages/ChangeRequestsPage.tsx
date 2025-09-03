import { FC, ReactNode, useEffect, useState } from 'react'
import OrganisationStore from 'common/stores/organisation-store'
import { RouterChildContext, useHistory } from 'react-router'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import ProjectStore from 'common/stores/project-store'
import {
  ChangeRequestSummary,
  Environment,
  PagedResponse,
  User,
} from 'common/types/responses'
import Utils from 'common/utils/utils'
import { Link } from 'react-router-dom'
import PageTitle from 'components/PageTitle'
import PlanBasedAccess, {
  featureDescriptions,
} from 'components/PlanBasedAccess'
import InfoMessage from 'components/InfoMessage'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import ConfigProvider from 'common/providers/ConfigProvider'
import ChangeRequestList from 'components/ChangeRequestsList'

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
  const history = useHistory()
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
          To enable this feature see <strong>Feature Change Requests</strong> in{' '}
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
                    {!!changeRequests?.count && (
                      <div className='counter-value ml-1'>
                        {changeRequests.count}
                      </div>
                    )}
                  </span>
                }
              >
                <ChangeRequestList
                  items={changeRequests}
                  page={page}
                  setPage={setPage}
                  isLoading={isLoading}
                  changeRequests={changeRequests}
                  getLink={getLink}
                  users={users}
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
                <ChangeRequestList
                  items={committedChangeRequests}
                  page={pageCommitted}
                  setPage={setPageCommitted}
                  isLoading={isLoading}
                  changeRequests={committedChangeRequests}
                  getLink={getLink}
                  users={users}
                />
              </TabItem>
            </Tabs>
          </div>
        </Flex>
      </PlanBasedAccess>
    </div>
  )
}

export default ConfigProvider(ChangeRequestsPage)
