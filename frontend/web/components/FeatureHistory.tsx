import React, { FC, useState } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useGetFeatureVersionsQuery } from 'common/services/useFeatureVersion'
import { useGetUsersQuery } from 'common/services/useUser'
import AccountStore from 'common/stores/account-store'
import { FeatureVersion as TFeatureVersion } from 'common/types/responses'
import Button from './base/forms/Button'
import FeatureVersion from './FeatureVersion'
import InlineModal from './InlineModal'
import TableFilterItem from './tables/TableFilterItem'
import moment from 'moment'
import DateList from './DateList'
import PlanBasedBanner from './PlanBasedAccess'
import classNames from 'classnames'
import PlanBasedBanner from 'components/PlanBasedAccess'

const widths = [250, 150]
type FeatureHistoryPageType = {
  environmentId: string
  environmentApiKey: string
  projectId: string
  feature: number
}

const FeatureHistory: FC<FeatureHistoryPageType> = ({
  environmentApiKey,
  environmentId,
  feature,
  projectId,
}) => {
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
    { skip: !environmentId || !feature },
  )
  const [selected, setSelected] = useState<TFeatureVersion | null>(null)
  const live = data?.results?.[0]
  const [compareToLive, setCompareToLive] = useState(false)
  const [diff, setDiff] = useState<null | string>(null)
  const versionLimit = 3
  return (
    <div>
      <h5>Change History</h5>
      <div>
        View and rollback history of feature values, multivariate values and
        segment overrides.
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
          nextPage={() => setPage(page + 1)}
          prevPage={() => setPage(page + 1)}
          goToPage={setPage}
          dateProperty={'live_from'}
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
                      <a
                        href={`/project/${projectId}/environment/${environmentApiKey}/history/${v.uuid}/`}
                        target='_blank'
                        rel='noreferrer'
                      >
                        <Button
                          theme='text'
                          className='px-0 text-primary'
                          size='xSmall'
                        >
                          View Details
                        </Button>
                      </a>
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
                      projectId={`${projectId}`}
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

export default ConfigProvider(FeatureHistory)
