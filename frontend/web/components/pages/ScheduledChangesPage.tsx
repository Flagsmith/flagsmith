import { FC, useEffect, useMemo, useRef, useState } from 'react'
import moment from 'moment/moment'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import { RouterChildContext } from 'react-router'
import AccountStore from 'common/stores/account-store'
import ProjectStore from 'common/stores/project-store'
import { ChangeRequestSummary, Environment, User } from 'common/types/responses'
import OrganisationStore from 'common/stores/organisation-store'
import AppActions from 'common/dispatcher/app-actions'
import ChangeRequestStore from 'common/stores/change-requests-store'
import { Link } from 'react-router-dom'
import Utils from 'common/utils/utils'
import PageTitle from 'components/PageTitle'
import PlanBasedBanner, {
  featureDescriptions,
} from 'components/PlanBasedAccess'
import PanelSearch from 'components/PanelSearch'
import JSONReference from 'components/JSONReference'
import Icon from 'components/Icon'

type ScheduledChangesPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}
const ScheduledChangesPage: FC<ScheduledChangesPageType> = ({ match }) => {
  const { environmentId, projectId } = match.params
  const organisationId = AccountStore.getOrganisation()?.id
  const [_, setUpdate] = useState(Date.now())
  const [page, setPage] = useState(1)

  // @ts-ignore
  const organisation = OrganisationStore.model as any
  const users = organisation?.users as User[]

  const live_from_after = useMemo(() => {
    return new Date().toISOString()
  }, [])
  const { data: dataScheduled, isLoading } = useGetChangeRequestsQuery({
    committed: true,
    environmentId,
    live_from_after,
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
      {!!Utils.getPlansPermission('SCHEDULE_FLAGS') && (
        <PageTitle title={featureDescriptions.SCHEDULE_FLAGS.title}>
          {featureDescriptions.SCHEDULE_FLAGS.description}
        </PageTitle>
      )}
      <PlanBasedBanner feature={'SCHEDULE_FLAGS'} theme={'page'}>
        <Flex>
          {
            <div>
              <PanelSearch
                renderSearchWithNoResults
                id='users-list'
                title='Scheduled Changes'
                className='no-pad'
                isLoading={isLoading || !dataScheduled || !organisation}
                paging={dataScheduled}
                items={dataScheduled?.results}
                renderFooter={() => (
                  <JSONReference
                    className='mt-4 ml-3'
                    title={'Change Requests'}
                    json={dataScheduled?.results}
                  />
                )}
                nextPage={() => setPage(page + 1)}
                prevPage={() => setPage(page + 1)}
                goToPage={setPage}
                renderRow={({
                  created_at,
                  id,
                  title,
                  user: _user,
                }: ChangeRequestSummary) => {
                  const user = users?.find((v) => v.id === _user)
                  return (
                    <Link
                      to={`/project/${projectId}/environment/${environmentId}/scheduled-changes/${id}`}
                      className='flex-row list-item clickable'
                    >
                      <Flex className='table-column px-3'>
                        <div className='font-weight-medium'>{title}</div>
                        <div className='list-item-subtitle mt-1'>
                          Created{' '}
                          {moment(created_at).format('Do MMM YYYY HH:mma')} by{' '}
                          {user && user.first_name} {user && user.last_name}
                        </div>
                      </Flex>
                      <div className='table-column'>
                        <Icon name='chevron-right' fill='#9DA4AE' width={20} />
                      </div>
                    </Link>
                  )
                }}
              />
            </div>
          }
        </Flex>
      </PlanBasedBanner>
    </div>
  )
}

export default ScheduledChangesPage
