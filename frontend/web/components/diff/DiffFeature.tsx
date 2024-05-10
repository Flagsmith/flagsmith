import React, { FC, useEffect, useState } from 'react'
import { FeatureState } from 'common/types/responses'
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

type FeatureDiffType = {
  oldState: FeatureState[]
  newState: FeatureState[]
  noChangesMessage?: string
  featureId: number
  projectId: string
  tabTheme?: string
  disableSegments?: boolean
}

const DiffFeature: FC<FeatureDiffType> = ({
  disableSegments,
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
  const { totalChanges } = diff
  const [value, setValue] = useState(0)

  const { data: segments } = useGetSegmentsQuery({
    projectId,
  })

  const segmentDiffs = disableSegments
    ? { diffs: [], totalChanges: 0 }
    : getSegmentDiff(oldState, newState, segments?.results)
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
                <div>
                  Value
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
                      <div className='table-column flex flex-1'>
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
                  <div>
                    Segment Overrides
                    {!!segmentDiffs.totalChanges && (
                      <span className='unread'>
                        {segmentDiffs.totalChanges}
                      </span>
                    )}
                  </div>
                }
              >
                <DiffSegments diffs={segmentDiffs.diffs} />
              </TabItem>
            )}
          </Tabs>
        </>
      )}
    </div>
  )
}

export default DiffFeature
