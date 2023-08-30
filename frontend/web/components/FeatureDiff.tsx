import React, { FC, useState } from 'react'
import { FeatureState, ProjectFlag, Segment } from 'common/types/responses'
import Utils from 'common/utils/utils'
import { Change } from 'diff'
import classNames from 'classnames'
import Format from 'common/utils/format'
import Switch from './Switch'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'
import {
  useGetProjectFlagQuery,
  useGetProjectFlagsQuery,
} from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import { sortBy, uniq } from 'lodash'

const Diff = require('diff')

type FeatureDiffType = {
  oldState: FeatureState[]
  newState: FeatureState[]
  featureId: string
  projectId: string
  oldTitle?: string
  newTitle?: string
}

type DiffType = {
  changes: Change[]
  isEnabledState?: boolean
}

const getChangedChanges = (changes: Change[]) =>
  changes.filter((v) => !!v.added || !!v.removed)

const DiffEl: FC<DiffType> = ({ changes, isEnabledState }) => {
  return (
    <>
      {changes.map((v, i) => (
        <div
          key={i}
          className={classNames('git-diff', {
            'git-diff--added': v.added,
            'git-diff--removed': v.removed,
          })}
        >
          {(!!v.added || !!v.removed) && (
            <span style={{ width: 30 }} className='text-center d-inline-block'>
              {v.added ? '+' : '-'}
            </span>
          )}
          {isEnabledState && (v.value === 'true' || v.value === 'false') ? (
            <Switch checked={v.value === 'true'} />
          ) : (
            v.value !== 'null' &&
            v.value !== 'undefined' && (
              <span
                dangerouslySetInnerHTML={{
                  __html: v.value
                    .replace(/ /g, '&nbsp;')
                    .replace(
                      /\n/g,
                      '<br/><span class="d-inline-block" style="width: 30px;"></span>',
                    ),
                }}
              />
            )
          )}
        </div>
      ))}
    </>
  )
}
const getDiff = (
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
) => {
  const oldEnabled = `${!!oldFeatureState?.enabled}`
  const newEnabled = `${!!newFeatureState?.enabled}`

  const diff = {
    enabled: Diff.diffLines(oldEnabled, newEnabled),
    value: Diff.diffLines(
      `${Utils.getTypedValue(
        Utils.featureStateToValue(oldFeatureState?.feature_state_value),
      )}`,
      `${Utils.getTypedValue(
        Utils.featureStateToValue(newFeatureState?.feature_state_value),
      )}`,
    ),
  }

  const valueChanges = getChangedChanges(diff.value).length ? 1 : 0
  const enabledChanges = getChangedChanges(diff.enabled).length ? 1 : 0
  const totalChanges = valueChanges + enabledChanges
  return { ...diff, totalChanges }
}

type TSegmentDiff = {
  name: Change[]
  priority: Change[]
  value: Change[]
  enabled: Change[]
  totalChanges: number
}
const REMOVED_KEY = '$REMOVED'
const getSegmentDiff = (
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
  segmentName: string,
) => {
  const oldName = oldFeatureState ? segmentName : ''
  const oldEnabled = oldFeatureState ? `${!!oldFeatureState?.enabled}` : ''
  const oldPriority = oldFeatureState?.feature_segment
    ? `${oldFeatureState.feature_segment.priority + 1}`
    : ''
  const newPriority = newFeatureState?.feature_segment
    ? `${newFeatureState.feature_segment.priority + 1}`
    : ''
  const newEnabled = newFeatureState
    ? `${!!newFeatureState?.enabled}`
    : REMOVED_KEY

  const newName = newFeatureState ? segmentName : REMOVED_KEY

  const diff = {
    enabled: Diff.diffLines(oldEnabled, newEnabled),
    name: Diff.diffLines(oldName, newName),
    priority: Diff.diffLines(oldPriority, newPriority),
    value: Diff.diffLines(
      `${Utils.getTypedValue(
        oldFeatureState
          ? Utils.featureStateToValue(oldFeatureState?.feature_state_value)
          : '',
      )}`,
      `${Utils.getTypedValue(
        newFeatureState
          ? Utils.featureStateToValue(newFeatureState?.feature_state_value)
          : REMOVED_KEY,
      )}`,
    ),
  }

  const valueChanges = getChangedChanges(diff.value).length ? 1 : 0
  const enabledChanges = getChangedChanges(diff.enabled).length ? 1 : 0
  const priorityChanges = getChangedChanges(diff.priority).length ? 1 : 0
  const totalChanges = valueChanges + enabledChanges + priorityChanges
  return { ...diff, totalChanges } as TSegmentDiff
}

type VariationDiffType = {}

const VariationDiff: FC<VariationDiffType> = ({}) => {
  return <></>
}

type SegmentsDiffType = {
  diffs: TSegmentDiff[] | undefined
}

const SegmentsDiff: FC<SegmentsDiffType> = ({ diffs }) => {
  return diffs ? (
    <div>
      <div className='flex-row table-header'>
        <div className='table-column flex flex-1 text-center'>Segment</div>
        <div className='table-column text-center' style={{ width: 80 }}>
          Priority
        </div>
        <div className='table-column' style={{ width: 300 }}>
          Value
        </div>
        <div className='table-column' style={{ width: 100 }}>
          Enabled
        </div>
      </div>
      {diffs.map((diff, i) => {
        return (
          <div key={i} className='list-item flex-row'>
            <div className='table-column flex flex-1' style={{ width: 100 }}>
              <DiffEl changes={diff.name} />
            </div>
            <div className='table-column text-center' style={{ width: 80 }}>
              <DiffEl changes={diff.priority} />
            </div>
            <div className='table-column' style={{ width: 300 }}>
              <DiffEl changes={diff.value} />
            </div>
            <div className='table-column' style={{ width: 100 }}>
              <DiffEl isEnabledState changes={diff.enabled} />
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

  const diff = getDiff(oldEnv, newEnv)
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
                  <span className='unread'>{totalSegmentChanges}</span>
                ) : (
                  <span className='text-muted float-right fw-normal fs-captionXSmall'>
                    No Changes
                  </span>
                )}
              </div>
            }
          >
            <div>
              {totalChanges === 0 && (
                <div className='p-4 text-center text-muted'>No Changes</div>
              )}
              <div className='flex-row table-header'>
                <div
                  className='table-column text-center'
                  style={{ width: 100 }}
                >
                  Enabled
                </div>
                <div className='table-column flex flex-1'>Value</div>
              </div>
              <div className='flex-row list-item'>
                <div
                  className='table-column text-center'
                  style={{ width: 100 }}
                >
                  <DiffEl isEnabledState changes={diff.enabled} />
                </div>
                <div className='table-column flex flex-1'>
                  <div>
                    <DiffEl changes={diff?.value} />
                  </div>
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
                {totalSegmentChanges ? (
                  <span className='unread'>{totalSegmentChanges}</span>
                ) : (
                  <span className='text-muted float-right fw-normal fs-captionXSmall'>
                    No Changes
                  </span>
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
