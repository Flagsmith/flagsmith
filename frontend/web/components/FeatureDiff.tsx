import React, { FC, useMemo, useState } from 'react'
import { FeatureState } from 'common/types/responses'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import { sortBy } from 'lodash'
import {
  getFeatureStateDiff,
  getSegmentDiff,
  TSegmentDiff,
} from './diff/diff-utils'
import DiffString from './diff/DiffString'
import DiffEnabled from './diff/DiffEnabled'
import DiffPriority from './diff/DiffPriority'
import diffString from './diff/DiffString'

type FeatureDiffType = {
  oldState: FeatureState[]
  newState: FeatureState[]
  featureId: string
  projectId: string
  oldTitle?: string
  newTitle?: string
}

type SegmentsDiffType = {
  diffs: TSegmentDiff[] | undefined
}

type SegmentDiffType = {
  diff: TSegmentDiff
}

const widths = [80, 80]
const SegmentDiff: FC<SegmentDiffType> = ({ diff }) => {
  return (
    <div className={'flex-row list-item list-item-sm'}>
      <div style={{ width: widths[0] }} className='table-column'>
        <DiffPriority
          oldValue={diff.created ? diff.newPriority : diff.oldPriority}
          newValue={diff.deleted ? diff.oldPriority : diff.newPriority}
        />
      </div>
      <div className='table-column flex-fill'>
        <DiffString
          oldValue={diff.created ? diff.newValue : diff.oldValue}
          newValue={diff.deleted ? diff.oldValue : diff.newValue}
        />
      </div>
      <div style={{ width: widths[1] }} className='table-column'>
        <DiffEnabled
          oldValue={diff.oldEnabled}
          newValue={diff.deleted ? diff.oldEnabled : diff.newEnabled}
        />
      </div>
    </div>
  )
}

export default SegmentDiff

const SegmentsDiff: FC<SegmentsDiffType> = ({ diffs }) => {
  const { created, deleted, modified, unChanged } = useMemo(() => {
    const created = []
    const deleted = []
    const modified = []
    const unChanged = []

    sortBy(diffs || [], (diff) => diff.newPriority)?.forEach((diff) => {
      if (diff.created) {
        created.push(diff)
      } else if (diff.deleted) {
        deleted.push(diff)
      } else if (diff.totalChanges) {
        deleted.push(diff)
      } else {
        unChanged.push(diff)
      }
    })
    return { created, deleted, modified, unChanged }
  }, [diffs])

  const tableHeader = (
    <Row className='table-header'>
      <div style={{ width: widths[0] }} className='table-column'>
        Priority
      </div>
      <div className='table-column flex-fill'>Value</div>
      <div style={{ width: widths[1] }} className='table-column'>
        Enabled
      </div>
    </Row>
  )

  return (
    <Tabs className='mt-4' uncontrolled theme='pill'>
      {!!created.length && (
        <TabItem
          tabLabel={
            <div>
              Created <div className='unread'>{created.length}</div>
            </div>
          }
        >
          {tableHeader}
          {created.map((diff, i) => (
            <SegmentDiff key={i} diff={diff} />
          ))}
        </TabItem>
      )}
      {!!deleted.length && (
        <TabItem
          tabLabel={
            <div>
              Deleted <div className='unread'>{deleted.length}</div>
            </div>
          }
        >
          {tableHeader}
          {deleted.map((diff, i) => (
            <SegmentDiff key={i} diff={diff} />
          ))}
        </TabItem>
      )}
      {!!modified.length && (
        <TabItem
          tabLabel={
            <div>
              Modified <div className='unread'>{modified.length}</div>
            </div>
          }
        >
          {tableHeader}
          {modified.map((diff, i) => (
            <SegmentDiff key={i} diff={diff} />
          ))}
        </TabItem>
      )}
      {!!unChanged.length && (
        <TabItem
          tabLabel={
            <div>
              Unchanged <div className='unread'>{unChanged.length}</div>
            </div>
          }
        >
          {tableHeader}
          {unChanged.map((diff, i) => (
            <SegmentDiff key={i} diff={diff} />
          ))}
        </TabItem>
      )}
    </Tabs>
  )

  return diffs ? (
    <div className={'mt-4'}>
      <div className='flex-row table-header'>
        <div className='table-column flex flex-1 text-center'>Segment</div>
        <div className='table-column text-center' style={{ width: 80 }}>
          Priority
        </div>
        <div className='table-column' style={{ width: 100 }}>
          Enabled
        </div>
        <div className='table-column' style={{ width: 300 }}>
          Value
        </div>
      </div>
      {diffs.map((diff, i) => {
        return (
          <div key={i} className='list-item flex-row'>
            <div className='table-column flex flex-1' style={{ width: 100 }}>
              {/*<DiffEl changes={diff.name} />*/}
            </div>
            <div className='table-column text-center' style={{ width: 80 }}>
              {/*<DiffEl changes={diff.priority} />*/}
            </div>
            <div className='table-column' style={{ width: 300 }}>
              <DiffString oldValue={diff.oldValue} newValue={diff.newValue} />
            </div>
            <div className='table-column' style={{ width: 100 }}>
              <DiffEnabled
                oldValue={diff.oldEnabled}
                newValue={diff.newEnabled}
              />
            </div>
          </div>
        )
      })}
    </div>
  ) : (
    <div className={'text-center'}>
      <Loader />
    </div>
  )
}

const FeatureDiff: FC<FeatureDiffType> = ({
  featureId,
  newState,
  newTitle,
  oldState,
  oldTitle,
  projectId,
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
  const relatedSegments = sortBy(
    segments?.results?.filter((segment) => {
      return newState
        .concat(oldState)
        .find((v) => v.feature_segment?.segment === segment.id)
    }),
    (s) => s.name,
  )
  let totalSegmentChanges = 0
  const segmentDiffs = relatedSegments.map((segment) => {
    const diff = getSegmentDiff(
      oldState?.find((v) => v.feature_segment?.segment === segment.id),
      newState?.find((v) => v.feature_segment?.segment === segment.id),
      segment.name,
    )
    if (diff.totalChanges) {
      totalSegmentChanges += 1
    }
    return diff
  })
  return (
    <div className='p-2'>
      {!feature ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <Tabs onChange={setValue} value={value}>
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
          {!!feature?.multivariate_options.length && (
            <TabItem tabLabel={'Variations'}></TabItem>
          )}
          <TabItem
            tabLabel={
              <div>
                Segment Overrides
                {!!totalSegmentChanges && (
                  <span className='unread'>{totalSegmentChanges}</span>
                )}
              </div>
            }
          >
            <SegmentsDiff diffs={segmentDiffs} />
          </TabItem>
        </Tabs>
      )}
    </div>
  )
}

export default FeatureDiff
