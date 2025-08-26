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
  if (rule?.type === 'ALL') return null
  return (
    <Row
      className={classNames(
        'and-divider',
        {
          'text-danger': rule.type !== 'ANY',
        },
        className || 'my-1',
      )}
    >
      <Flex className='and-divider__line' />
      {Format.camelCase(
        `${index > 0 ? 'And ' : ''}${
          rule.type === 'ANY' ? 'Any of the following' : 'None of the following'
        }`,
      )}
      <Flex className='and-divider__line' />
    </Row>
  )
}

export default SegmentRuleDivider
