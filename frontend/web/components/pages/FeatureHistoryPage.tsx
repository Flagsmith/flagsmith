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
import { FeatureVersion } from 'common/types/responses'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import FeatureDiff from 'components/FeatureDiff'
import FeatureVersionDiff from 'components/FeatureVersionDiff' // we need this to make JSX compile

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
  // @ts-ignore
  const environmentId = `${env?.id}`
  const { data: users } = useGetUsersQuery({
    organisationId: AccountStore.getOrganisation().id,
  })
  const [page, setPage] = useState(1)
  const { data } = useGetFeatureVersionsQuery(
    {
      environmentId,
      featureId: feature,
      page,
    },
    { skip: !env || !feature },
  )
  const live = data?.results?.[0]

  const [diff, setDiff] = useState<null | string>(null)

  return (
    <div className='container app-container'>
      <PageTitle title={'Feature Versions'}>
        <div>
          View and rollback history of feature values, multivariate values and
          segment overrides.
        </div>
      </PageTitle>
      <div className='row'>
        <div className='col-md-4'>
          <div className='flex-row'>
            <label className='mb-0'>Feature</label>
            <div className='flex-fill ml-2'>
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
        </div>
      </div>
      <div>
        <PanelSearch
          className='no-pad'
          items={data?.results}
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
          renderRow={(v: FeatureVersion, i) => {
            const user = users?.find((user) => v.published_by === user.id)

            return (
              <Row className='list-item py-2 mh-auto'>
                <div className='flex-fill'>
                  <div className='flex-row flex-fill'>
                    <div className='table-column' style={{ width: widths[0] }}>
                      {moment(v.live_from).format('Do MMM HH:mma')}
                      {!i && <span className='chip ms-2'>Live</span>}
                    </div>
                    <div className='table-column text-left flex-fill'>
                      {user
                        ? `${user.first_name || ''} ${user.last_name || ''} `
                        : 'System '}
                    </div>

                    <div className='table-column' style={{ width: widths[1] }}>
                      {i + 1 !== data!.results.length && (
                        <Button
                          onClick={() =>
                            setDiff(diff === v.uuid ? null : v.uuid)
                          }
                          className='px-0 text-primary'
                          theme='text'
                          size='xSmall'
                        >
                          {diff === v.uuid ? 'Hide' : 'View'} Changes
                        </Button>
                      )}
                    </div>
                  </div>
                  {diff === v.uuid && (
                    <FeatureVersionDiff
                      featureId={feature}
                      environmentId={environmentId}
                      newUUID={v.uuid}
                      oldUUID={data!.results[i + 1]!.uuid}
                    />
                  )}
                </div>
              </Row>
            )
          }}
        />
      </div>
    </div>
  )
}

export default ConfigProvider(FeatureHistoryPage)
