import React, { FC } from 'react'
import classNames from 'classnames'
import Format from 'common/utils/format'
import { SegmentRule } from 'common/types/responses'

type SegmentRuleDividerType = {
  rule: SegmentRule
  index: number
}

const SegmentRuleDivider: FC<SegmentRuleDividerType> = ({ index, rule }) => {
  return (
    <Row
      className={classNames('and-divider my-1', {
        'text-danger': rule.type !== 'ANY',
      })}
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
