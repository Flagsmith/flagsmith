import { shouldMeasureAgain } from 'common/hooks/useOverflowVisibleCount'

const container = { name: 'container' }
const item = { name: 'item' }

describe('shouldMeasureAgain', () => {
  it.each`
    changed              | isOverflowing | expected | case
    ${[item]}            | ${false}      | ${true}  | ${'a change inside an item'}
    ${[container]}       | ${false}      | ${false} | ${'items shown or hidden that fit'}
    ${[container]}       | ${true}       | ${true}  | ${'a shown item that no longer fits'}
    ${[container, item]} | ${false}      | ${true}  | ${'a mix including an item change'}
  `('returns $expected for $case', ({ changed, expected, isOverflowing }) => {
    expect(shouldMeasureAgain(changed, container, isOverflowing)).toBe(expected)
  })
})
