import React, { FC, useState } from 'react'
import FlagSelect from 'components/FlagSelect'
import ConfigProvider from 'common/providers/ConfigProvider'
import { RouterChildContext } from 'react-router'
import Utils from 'common/utils/utils'
import ProjectStore from 'common/stores/project-store'
import { useGetFeatureVersionsQuery } from 'common/services/useFeatureVersion'
import { useGetUsersQuery } from 'common/services/useUser'
import AccountStore from 'common/stores/account-store'
import {
  Environment,
  FeatureVersion as TFeatureVersion,
} from 'common/types/responses'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import FeatureVersion from 'components/FeatureVersion'
import InlineModal from 'components/InlineModal'
import TableFilterItem from 'components/tables/TableFilterItem'
import moment from 'moment'
import { Link } from 'react-router-dom'
import DateList from 'components/DateList'
import classNames from 'classnames'
import PlanBasedBanner from 'components/PlanBasedAccess'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'

const widths = [250, 150]
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
  const [open, setOpen] = useState(false)
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery({
    id: AccountStore.getOrganisation()?.id,
  })
  const versionLimitDays = subscriptionMeta?.feature_history_visibility_days
  const env: Environment | undefined = ProjectStore.getEnvironment(
    match.params.environmentId,
  ) as any
  // @ts-ignore
  const environmentId = `${env?.id}`
  const environmentApiKey = `${env?.api_key}`
  const { data: users } = useGetUsersQuery({
    organisationId: AccountStore.getOrganisation().id,
  })
  const [page, setPage] = useState(1)
  const { data, isLoading } = useGetFeatureVersionsQuery(
    {
      environmentId,
      featureId: feature,
      is_live: true,
      page,
    },
    { skip: !env || !feature },
  )
  const [selected, setSelected] = useState<TFeatureVersion | null>(null)
  const live = data?.results?.[0]
  const [compareToLive, setCompareToLive] = useState(false)
  const [diff, setDiff] = useState<null | string>(null)
  return (
    <div className='container app-container'>
      <PageTitle title={'History'}>
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
      <div className='mt-4'>
        {!!versionLimitDays && (
          <PlanBasedBanner
            className='mb-4'
            force
            feature={'VERSIONING'}
            title={
              <div>
                Unlock your feature's entire history. Currently limited to{' '}
                <strong>{versionLimitDays} days</strong>.
              </div>
            }
            theme={'page'}
          />
        )}
        <DateList<TFeatureVersion>
          items={data}
          isLoading={isLoading}
          dateProperty={'live_from'}
          nextPage={() => setPage(page + 1)}
          prevPage={() => setPage(page + 1)}
          goToPage={setPage}
          renderRow={(v: TFeatureVersion, i: number) => {
            const user = users?.find((user) => v.published_by === user.id)

            return (
              <Row className={classNames('list-item py-2 mh-auto')}>
                <div className='flex-fill'>
                  <div className='flex-row flex-fill'>
                    <div
                      className='table-column flex-fill'
                      style={{ width: widths[0] }}
                    >
                      <div className='font-weight-medium d-flex gap-2 align-items-center mb-1'>
                        {moment(v.live_from).format('HH:mma')}
                        <div className='text-muted fw-normal text-small'>
                          {user
                            ? `${user.first_name || ''} ${
                                user.last_name || ''
                              } `
                            : 'System '}
                        </div>
                        {!i && <span className='chip chip--xs px-2'>Live</span>}
                      </div>
                    </div>
                    <div className='table-column' style={{ width: widths[1] }}>
                      <Link
                        to={`/project/${match.params.projectId}/environment/${environmentApiKey}/history/${v.uuid}/`}
                      >
                        <Button
                          theme='text'
                          className='px-0 text-primary'
                          size='xSmall'
                        >
                          View Details
                        </Button>
                      </Link>
                    </div>
                    <div className='table-column' style={{ width: widths[1] }}>
                      {i + 1 !== data!.results.length && (
                        <>
                          {diff === v.uuid ? (
                            <Button
                              data-test={`history-item-${i}-hide`}
                              onClick={() => {
                                setSelected(null)
                                setDiff(diff === v.uuid ? null : v.uuid)
                              }}
                              className='px-0 text-primary'
                              theme='text'
                              size='xSmall'
                            >
                              Hide Changes
                            </Button>
                          ) : (
                            <div>
                              <Button
                                data-test={`history-item-${i}-compare`}
                                onClick={() => {
                                  if (v.uuid === live!.uuid) {
                                    setCompareToLive(false)
                                    setDiff(v.uuid)
                                  } else {
                                    setSelected(v)
                                    // setDiff(diff === v.uuid ? null : v.uuid)
                                    setOpen(true)
                                  }
                                }}
                                className='px-0 text-primary'
                                theme='text'
                                size='xSmall'
                              >
                                Quick compare
                              </Button>
                            </div>
                          )}
                        </>
                      )}
                      <InlineModal
                        hideClose
                        title={null}
                        isOpen={open && selected === v}
                        onClose={() => {
                          setTimeout(() => {
                            setOpen(false)
                          }, 10)
                        }}
                        containerClassName='px-0'
                        className='inline-modal table-filter inline-modal--sm right'
                      >
                        <TableFilterItem
                          data-test={`history-item-${i}-compare-live`}
                          title={'Live Version'}
                          onClick={() => {
                            setCompareToLive(true)
                            if (selected) {
                              setDiff(
                                diff === selected.uuid ? null : selected.uuid,
                              )
                            }
                            setOpen(false)
                          }}
                        />
                        <TableFilterItem
                          data-test={`history-item-${i}-compare-previous`}
                          title={'Previous Version'}
                          onClick={() => {
                            setCompareToLive(false)
                            if (selected) {
                              setDiff(
                                diff === selected.uuid ? null : selected.uuid,
                              )
                            }
                            setOpen(false)
                          }}
                        />
                      </InlineModal>
                    </div>
                  </div>
                  {diff === v.uuid && (
                    <FeatureVersion
                      projectId={`${match.params.projectId}`}
                      featureId={feature}
                      environmentId={environmentId}
                      newUUID={compareToLive ? live!.uuid : v.uuid}
                      oldUUID={
                        compareToLive
                          ? data!.results[i]!.uuid
                          : data!.results[i + 1]!.uuid
                      }
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
