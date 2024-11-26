import {
  getSegmentDiff,
  TDiffSegmentOverride,
  TSegmentRuleDiff,
} from './diff-utils'
import React, { FC, useMemo } from 'react'
import { Segment } from 'common/types/responses'
import SegmentRuleDivider from 'components/SegmentRuleDivider'

type DiffSegmentOverride = {
  diff: TDiffSegmentOverride
  oldSegment: Segment
  newSegment: Segment
}

type DiffRuleType = {
  diff: TSegmentRuleDiff
  index: number
}

const DiffRule: FC<DiffRuleType> = ({ diff, index }) => {
  const rule = (diff.newRule || diff.oldRule)!
  return (
    <>
      <SegmentRuleDivider rule={rule} index={index} />
    </>
  )
}

const DiffSegmentOverride: FC<DiffSegmentOverride> = ({
  newSegment,
  oldSegment,
}) => {
  const diff = useMemo(() => {
    return getSegmentDiff(oldSegment, newSegment)
  }, [oldSegment, newSegment])

  return (
    <div>
      {!diff.totalChanges && 'No Changes'}
      {diff.changes?.map((diff, index) => (
        <DiffRule key={index} diff={diff} index={index} />
      ))}
    </div>
  )
}

export default DiffSegmentOverrides
