import React, { FC, useEffect, useState } from 'react'
import {
  FeatureConflict,
  FeatureStateWithConflict,
} from 'common/types/responses'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import {
  getFeatureStateDiff,
  getSegmentOverrideDiff,
  getVariationDiff,
} from './diff-utils'
import DiffString from './DiffString'
import DiffEnabled from './DiffEnabled'
import DiffSegmentOverrides from './DiffSegmentOverrides'
import DiffVariations from './DiffVariations'
import InfoMessage from 'components/InfoMessage'
import Icon from 'components/Icon'
import WarningMessage from 'components/WarningMessage'
import { Link } from 'react-router-dom'

type FeatureDiffType = {
  oldState: FeatureStateWithConflict[]
  newState: FeatureStateWithConflict[]
  noChangesMessage?: string
  featureId: number
  projectId: string
  environmentId: string
  tabTheme?: string
  conflicts?: FeatureConflict[] | undefined
  disableSegments?: boolean
}
const enabledWidth = 110
const DiffFeature: FC<FeatureDiffType> = ({
  conflicts,
  disableSegments,
  environmentId,
  featureId,
  newState,
  noChangesMessage,
  oldState,
  projectId,
  tabTheme,
}) => {
  const { data: projectFlag } = useGetProjectFlagQuery({
    id: featureId,
    project: projectId,
  })

  const oldEnv = oldState?.find((v) => !v.feature_segment)
  const newEnv = newState?.find((v) => !v.feature_segment)
  const { data: feature } = useGetProjectFlagQuery({
    id: `${featureId}`,
    project: projectId,
  })

  const diff = getFeatureStateDiff(oldEnv, newEnv)
  const { conflict: valueConflict, totalChanges } = diff
  const [value, setValue] = useState(0)
  const [viewMode, setViewMode] = useState<'combined' | 'new' | 'old'>(
    'combined',
  )

  const { data: segments } = useGetSegmentsQuery({
    include_feature_specific: true,
    page_size: 1000,
    projectId,
  })

  const segmentDiffs = disableSegments
    ? { diffs: [], totalChanges: 0 }
    : getSegmentOverrideDiff(oldState, newState, segments?.results, conflicts)
  const variationDiffs = getVariationDiff(oldEnv, newEnv)
  const totalSegmentChanges = segmentDiffs?.totalChanges
  const totalVariationChanges = variationDiffs?.totalChanges
  useEffect(() => {
    if (!totalChanges && (totalSegmentChanges || totalVariationChanges)) {
      setValue(1)
    }
  }, [totalSegmentChanges, totalVariationChanges, totalChanges])
  const hideValue =
    !totalChanges && (diff.newValue === null || diff.newValue === undefined)
  return (
    <div>
      {!feature ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <>
          {!totalChanges &&
            !totalSegmentChanges &&
            !totalVariationChanges &&
            noChangesMessage && <InfoMessage>{noChangesMessage}</InfoMessage>}
          <Tabs
            hideNavOnSingleTab
            theme={tabTheme}
            onChange={setValue}
            value={value}
            cta={
              <div className='d-flex align-items-center gap-2'>
                <label className='mb-0'>View</label>
                <div style={{ width: 150 }}>
                  <Select
                    size='select-xsm'
                    value={{
                      label:
                        viewMode === 'combined'
                          ? 'Combined Diff'
                          : viewMode === 'new'
                          ? 'New Value'
                          : 'Old Value',
                      value: viewMode,
                    }}
                    options={[
                      { label: 'Combined Diff', value: 'combined' },
                      { label: 'New Value', value: 'new' },
                      { label: 'Old Value', value: 'old' },
                    ]}
                    onChange={(option: { value: 'combined' | 'new' | 'old' }) =>
                      setViewMode(option.value)
                    }
                  />
                </div>
              </div>
            }
          >
            <TabItem
              className={'p-0'}
              tabLabel={
                <div className='d-flex justify-content-center gap-1 align-items-center'>
                  Value
                  {!!valueConflict && <Icon width={16} name='warning' />}
                  {totalChanges ? (
                    <span className='unread'>{totalChanges}</span>
                  ) : null}
                </div>
              }
            >
              {!!valueConflict && (
                <div className='mt-4'>
                  <WarningMessage
                    warningMessage={
                      <div>
                        A change request was published since the creation of
                        this one that also modified the value.
                        <br />
                        Please review the following changes to make sure they
                        are correct.
                        <div>
                          <Link
                            to={`/project/${projectId}/environment/${environmentId}/change-requests/${valueConflict.original_cr_id}`}
                          >
                            View published change request
                          </Link>
                        </div>
                      </div>
                    }
                  />
                </div>
              )}
              <div className='panel-content'>
                <div className='search-list mt-2'>
                  <div className='flex-row gap-5 table-header'>
                    <div
                      style={{ width: enabledWidth }}
                      className='table-column flex-row text-center'
                    >
                      Enabled
                    </div>
                    {!hideValue && (
                      <div className='table-column flex-row flex flex-1'>
                        Value
                      </div>
                    )}
                  </div>
                  <div className='flex-row pt-4 gap-5 list-item list-item-sm'>
                    <div
                      style={{ width: enabledWidth }}
                      className='table-column text-center'
                    >
                      <div className='d-flex flex-row'>
                        <DiffEnabled
                          data-test={'version-enabled'}
                          oldValue={
                            viewMode === 'new'
                              ? diff.newEnabled
                              : diff.oldEnabled
                          }
                          newValue={
                            viewMode === 'old'
                              ? diff.oldEnabled
                              : diff.newEnabled
                          }
                        />
                      </div>
                    </div>
                    {!hideValue && (
                      <div className='table-column flex flex-1 overflow-hidden'>
                        <div>
                          <DiffString
                            data-test={'version-value'}
                            oldValue={
                              viewMode === 'new' ? diff.newValue : diff.oldValue
                            }
                            newValue={
                              viewMode === 'old' ? diff.oldValue : diff.newValue
                            }
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </TabItem>
            {!!variationDiffs?.diffs?.length && (
              <TabItem
                className={'p-0'}
                tabLabel={
                  <div>
                    Variations{' '}
                    {variationDiffs.totalChanges ? (
                      <span className='unread'>
                        {variationDiffs.totalChanges}
                      </span>
                    ) : null}
                  </div>
                }
              >
                <DiffVariations
                  projectFlag={projectFlag}
                  diffs={variationDiffs.diffs}
                />
              </TabItem>
            )}
            {!!segmentDiffs?.diffs.length && (
              <TabItem
                className={'p-0'}
                tabLabel={
                  <div className='d-flex justify-content-center gap-1 align-items-center'>
                    Segment Overrides
                    {!!segmentDiffs.totalConflicts && (
                      <Icon width={16} name='warning' />
                    )}
                    {!!segmentDiffs.totalChanges && (
                      <span className='unread'>
                        {segmentDiffs.totalChanges}
                      </span>
                    )}
                  </div>
                }
              >
                {!!segmentDiffs.totalConflicts && (
                  <div className='mt-4'>
                    <WarningMessage
                      warningMessage={
                        <div>
                          A change request was published since the creation of
                          this one that also modified{' '}
                          {segmentDiffs.totalConflicts === 1 ? 'one' : 'some'}{' '}
                          of the segment overrides.
                          <br />
                          Please review the following changes to make sure they
                          are correct.
                        </div>
                      }
                    />
                  </div>
                )}
                <DiffSegmentOverrides
                  diffs={segmentDiffs.diffs}
                  projectId={projectId}
                  environmentId={environmentId}
                />
              </TabItem>
            )}
          </Tabs>
        </>
      )}
    </div>
  )
}

export default DiffFeature
