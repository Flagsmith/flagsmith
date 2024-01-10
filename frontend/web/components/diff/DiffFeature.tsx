import React, { FC, useState } from 'react'
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

type FeatureDiffType = {
  oldState: FeatureState[]
  newState: FeatureState[]
  featureId: number
  projectId: string
  tabTheme?: string
}

const DiffFeature: FC<FeatureDiffType> = ({
  featureId,
  newState,
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
  const [value, setValue] = useState(totalChanges ? 0 : 1)

  const { data: segments } = useGetSegmentsQuery({
    projectId,
  })

  const segmentDiffs = getSegmentDiff(oldState, newState, segments?.results)
  const variationDiffs = getVariationDiff(oldEnv, newEnv, feature)
  return (
    <div className='p-2'>
      {!feature ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
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
            <div>
              <div className='flex-row mt-4 table-header'>
                <div className='table-column flex-row flex flex-1'>Value</div>
                <div className='table-column flex-row text-center'>Enabled</div>
              </div>
              <div className='flex-row pt-4 list-item'>
                <div className='table-column flex flex-1'>
                  <div>
                    <DiffString
                      oldValue={diff.oldValue}
                      newValue={diff.newValue}
                    />
                  </div>
                </div>
                <div className='table-column text-center'>
                  <DiffEnabled
                    oldValue={diff.oldEnabled}
                    newValue={diff.newEnabled}
                  />
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
                    <span className='unread'>{segmentDiffs.totalChanges}</span>
                  )}
                </div>
              }
            >
              <DiffSegments diffs={segmentDiffs.diffs} />
            </TabItem>
          )}
        </Tabs>
      )}
    </div>
  )
}

export default DiffFeature
