import {
  getSegmentDiff,
  TSegmentConditionDiff,
  TSegmentRuleDiff,
} from './diff-utils'
import React, { FC, useMemo } from 'react'
import { Operator, Segment } from 'common/types/responses'
import SegmentRuleDivider from 'components/SegmentRuleDivider'
import DiffString from './DiffString'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'

type DiffSegmentType = {
  oldSegment: Segment
  newSegment: Segment
}

type DiffRuleType = {
  diff: TSegmentRuleDiff
  index: number
}

const DiffSegment: FC<DiffSegmentType> = ({ newSegment, oldSegment }) => {
  const diff = useMemo(() => {
    return getSegmentDiff(oldSegment, newSegment)
  }, [oldSegment, newSegment])

  return (
    <div>
      {!diff.totalChanges && 'No Changes'}
      {diff.changes?.map((diff, index) => (
        <>
          <DiffRule key={index} diff={diff} index={index} />
        </>
      ))}
    </div>
  )
}
type DiffConditionType = {
  diff: TSegmentConditionDiff
  index: number
}

const DiffCondition: FC<DiffConditionType> = ({ diff, index }) => {
  const operators: Operator[] | null = Utils.getSegmentOperators()
  const oldOperator = operators?.find((v) => v.value === diff?.old?.operator)
  const newOperator = operators?.find((v) => v.value === diff?.new?.operator)

  return (
    <div>
      <DiffString
        oldValue={`${diff.old?.property || ''} ${oldOperator?.label || ''} ${
          diff?.old?.value || ''
        }`}
        newValue={`${diff.new?.property || ''} ${newOperator?.label || ''} ${
          diff?.new?.value || ''
        }`}
      />
    </div>
  )
}
const DiffRule: FC<DiffRuleType> = ({ diff, index }) => {
  const rule = (diff.newRule || diff.oldRule)!
  return (
    <>
      <SegmentRuleDivider rule={rule} index={index} />
      {diff?.rules?.map((v, i) => (
        <>
          <DiffRule key={i} diff={v} index={i} />
        </>
      ))}
      {diff?.conditions?.map((v, i) => (
        <DiffCondition key={i} diff={v} index={i} />
      ))}
    </>
  )
}

export default DiffSegment
