import React, { FC } from 'react'
import classNames from 'classnames'
import Format from 'common/utils/format'
import { SegmentRule } from 'common/types/responses'

type SegmentRuleDividerType = {
  rule: SegmentRule
  index: number
  className?: string
}

const SegmentRuleDivider: FC<SegmentRuleDividerType> = ({
  className,
  index,
  rule,
}) => {
  if (rule?.type === 'ALL' && index === 0) return null
  const labels: Record<SegmentRule['type'], string> = {
    ALL: 'All of the following',
    ANY: 'Any of the following',
    NONE: 'None of the following',
  }
  const label = labels[rule.type]
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
      {Format.camelCase(`${index > 0 ? 'And ' : ''}${label}`)}
      <Flex className='and-divider__line' />
    </Row>
  )
}

export default SegmentRuleDivider
