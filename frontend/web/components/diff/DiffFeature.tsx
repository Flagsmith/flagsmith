import React, { FC, useEffect, useState } from 'react'
import {
  FeatureConflict,
  FeatureState,
  FeatureStateWithConflict,
} from 'common/types/responses'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import {
  getFeatureStateDiff,
  getSegmentDiff,
  getVariationDiff,
} from './diff-utils'
import DiffString from './DiffString'
import DiffEnabled from './DiffEnabled'
import DiffSegments from './DiffSegments'
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
  const oldEnv = oldState?.find((v) => !v.feature_segment)
  const newEnv = newState?.find((v) => !v.feature_segment)
  const { data: feature } = useGetProjectFlagQuery({
    id: `${featureId}`,
    project: projectId,
  })

  const diff = getFeatureStateDiff(oldEnv, newEnv)
  const { conflict: valueConflict, totalChanges } = diff
  const [value, setValue] = useState(0)

  const { data: segments } = useGetSegmentsQuery({
    include_feature_specific: true,
    page_size: 1000,
    projectId,
  })

  const segmentDiffs = disableSegments
    ? { diffs: [], totalChanges: 0 }
    : getSegmentDiff(oldState, newState, segments?.results, conflicts)
  const variationDiffs = getVariationDiff(oldEnv, newEnv, feature)
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
    <div className='p-2'>
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
          >
            <TabItem
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
              {!totalChanges && (
                <div className='mt-4'>
                  <InfoMessage>No Changes Found</InfoMessage>
                </div>
              )}
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
                  <div className='flex-row table-header'>
                    {!hideValue && (
                      <div className='table-column flex-row flex flex-1'>
                        Value
                      </div>
                    )}
                    <div className='table-column flex-row text-center'>
                      Enabled
                    </div>
                  </div>
                  <div className='flex-row pt-4 list-item list-item-sm'>
                    {!hideValue && (
                      <div className='table-column flex flex-1 overflow-hidden'>
                        <div>
                          <DiffString
                            data-test={'version-value'}
                            oldValue={diff.oldValue}
                            newValue={diff.newValue}
                          />
                        </div>
                      </div>
                    )}

                    <div className='table-column text-center'>
                      <DiffEnabled
                        data-test={'version-enabled'}
                        oldValue={diff.oldEnabled}
                        newValue={diff.newEnabled}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </TabItem>
            {!!variationDiffs?.diffs?.length && (
              <TabItem
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
                <DiffVariations diffs={variationDiffs.diffs} />
              </TabItem>
            )}
            {!!segmentDiffs?.diffs.length && (
              <TabItem
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
                <DiffSegments
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
