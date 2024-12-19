import {
  getSegmentDiff,
  TSegmentConditionDiff,
  TSegmentRuleDiff,
} from './diff-utils'
import React, { FC, useMemo } from 'react'
import { Operator, Segment } from 'common/types/responses'
import SegmentRuleDivider from 'components/SegmentRuleDivider'
import DiffString from './DiffString'
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
      <div className='d-flex flex-column ml-0 me-0 gap-3'>
        <div className='d-flex flex-column ml-0 me-0 gap-1'>
          <label>Name</label>
          <DiffString oldValue={oldSegment.name} newValue={newSegment.name} />
        </div>
        {(!!oldSegment.description || !!newSegment.description) && (
          <div className='d-flex flex-column ml-0 me-0 gap-1'>
            <label>Description</label>
            <DiffString
              oldValue={oldSegment.description}
              newValue={newSegment.description}
            />
          </div>
        )}
        <div className='d-flex ml-0 me-0 flex-column'>
          <label className='mb-0'>Rules</label>
          {diff.changes?.map((diff, index) => (
            <>
              <DiffRule key={index} diff={diff} index={index} />
            </>
          ))}
        </div>
      </div>
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
      <SegmentRuleDivider rule={rule} index={index} className='mt-0 mb-1' />
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
