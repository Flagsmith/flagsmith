import {
  DIFF_SEGMENT_MODES,
  getSegmentDiff,
  getSegmentDiffPair,
  TSegmentConditionDiff,
  TSegmentRuleDiff,
} from './diff-utils'
import React, { FC, useMemo, useState } from 'react'
import { Operator, Segment } from 'common/types/responses'
import SegmentRuleDivider from 'components/SegmentRuleDivider'
import DiffString from './DiffString'
import Utils from 'common/utils/utils'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'

type DiffSegmentType = {
  oldSegment: Segment
  newSegment: Segment
}

type DiffRuleType = {
  diff: TSegmentRuleDiff
  index: number
}
const DiffSegment: FC<DiffSegmentType> = ({ newSegment, oldSegment }) => {
  const [mode, setMode] = useState(0)

  const [a, b] = useMemo(
    () => getSegmentDiffPair(mode, oldSegment, newSegment),
    [mode, oldSegment, newSegment],
  )
  const diff = useMemo(() => {
    return getSegmentDiff(a, b)
  }, [a, b])
  return (
    <div>
      <Tabs onChange={setMode} className='mb-2' theme='pill' value={mode}>
        {Object.keys(DIFF_SEGMENT_MODES).map((key) => (
          <TabItem key={key} tabLabel={key} />
        ))}
      </Tabs>
      <div className='d-flex flex-column ml-0 me-0 gap-3'>
        <div className='d-flex flex-column ml-0 me-0 gap-1'>
          <label>Name</label>
          <DiffString oldValue={a.name} newValue={b.name} />
        </div>
        {(!!a.description || !!b.description) && (
          <div className='d-flex flex-column ml-0 me-0 gap-1'>
            <label>Description</label>
            <DiffString oldValue={a.description} newValue={b.description} />
          </div>
        )}
        <div className='d-flex ml-0 me-0 flex-column'>
          <label className='mb-0'>Rules</label>
          <DiffString oldValue={diff.oldString} newValue={diff.newString} />
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
        <div className='mb-2 p-2'>
          <DiffRule key={i} diff={v} index={i} />
        </div>
      ))}
      {diff?.conditions?.map((v, i) => (
        <>
          <DiffCondition key={i} diff={v} index={i} />
          {i + 1 !== diff?.conditions?.length && (
            <Row className='or-divider my-2'>
              <Row>
                <div className='or-divider__up' />
                Or
                <div className='or-divider__down' />
              </Row>
              <Flex className='or-divider__line' />
            </Row>
          )}
        </>
      ))}
    </>
  )
}

export default DiffSegment
