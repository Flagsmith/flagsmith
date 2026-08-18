import React, { FC } from 'react'
import classNames from 'classnames'
import Format from 'common/utils/format'
import { SegmentRule } from 'common/types/responses'

type SegmentRuleDividerType = {
  rule: SegmentRule
  index: number
  className?: string
  topLevelRuleType?: 'ALL' | 'ANY'
}

const typeLabel: Record<SegmentRule['type'], string> = {
  ALL: 'All of the following',
  ANY: 'Any of the following',
  NONE: 'None of the following',
}

const SegmentRuleDivider: FC<SegmentRuleDividerType> = ({
  className,
  index,
  rule,
  topLevelRuleType = 'ALL',
}) => {
  if (rule?.type === 'ALL' && topLevelRuleType === 'ALL') return null
  const connector = topLevelRuleType === 'ANY' ? 'Or' : 'And'
  const prefix = index > 0 ? `${connector} ` : ''
  return (
    <Row
      className={classNames(
        'and-divider',
        {
          'text-danger': rule.type === 'NONE',
        },
        className || 'my-1',
      )}
    >
      <Flex className='and-divider__line' />
      {Format.camelCase(`${prefix}${typeLabel[rule.type]}`)}
      <Flex className='and-divider__line' />
    </Row>
  )
}

export default SegmentRuleDivider
