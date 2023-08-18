import React, { FC, useState } from 'react'
import FlagSelect from 'components/FlagSelect'
import ConfigProvider from 'common/providers/ConfigProvider'
import { RouterChildContext } from 'react-router'
import Utils from 'common/utils/utils'
import ProjectStore from 'common/stores/project-store'
import { useGetFeatureVersionsQuery } from 'common/services/useFeatureVersion'
import { useGetUsersQuery } from 'common/services/useUser'
import AccountStore from 'common/stores/account-store'
import PanelSearch from 'components/PanelSearch'
import { FeatureVersion } from 'common/types/responses' // we need this to make JSX compile

const widths = [250, 100]
type FeatureHistoryPageType = {
  router: RouterChildContext['router']

  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const FeatureHistoryPage: FC<FeatureHistoryPageType> = ({ match, router }) => {
  const feature = Utils.fromParam(router.route.location.search)?.feature
  const env = ProjectStore.getEnvironment(match.params.environmentId)
  const { data: users } = useGetUsersQuery({
    organisationId: AccountStore.getOrganisation().id,
  })
  const [page, setPage] = useState(1)
  const { data } = useGetFeatureVersionsQuery(
    {
      environmentId: `${env?.id}`,
      featureId: feature,
      page,
      page_size: 10,
    },
    { skip: !env || !feature },
  )

  return (
    <div className='container app-container'>
      <div className='row'>
        <div className='col-md-4'>
          <FlagSelect
            placeholder='Select a Feature...'
            projectId={match.params.projectId}
            onChange={(flagId: string) => {
              router.history.replace(
                `${document.location.pathname}?feature=${flagId}`,
              )
            }}
            value={feature ? parseInt(feature) : null}
          />
        </div>
      </div>
      <div className='row'>
        <div></div>
        <div>
          <PanelSearch
            items={data?.results}
            paging={data}
            nextPage={() => setPage(page + 1)}
            prevPage={() => setPage(page - 1)}
            goToPage={setPage}
            header={
              <Row className='table-header'>
                <div className='table-column' style={{ width: widths[0] }}>
                  Date
                </div>
                <div className='table-column text-left flex-fill'>User</div>
                <div className='table-column' style={{ width: widths[1] }}>
                  View
                </div>
              </Row>
            }
            renderRow={(v: FeatureVersion) => {
              const user = users?.find((user) => v.published_by === user.id)

              return (
                <Row className='list-item list-item-sm'>
                  <div className='table-column' style={{ width: widths[0] }}>
                    {moment(v.live_from).format('Do MMM HH:mma')}
                    {v.is_live && <span className='chip ms-2'>Live</span>}
                  </div>
                  <div className='table-column text-left flex-fill'>
                    {user
                      ? `${user.first_name || ''} ${user.last_name || ''} `
                      : 'System '}
                  </div>
                  <div className='table-column' style={{ width: widths[1] }}>
                    View
                  </div>
                </Row>
              )
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default ConfigProvider(FeatureHistoryPage)
