import { isItemContentChange } from 'common/hooks/useOverflowVisibleCount'

const container = { name: 'container' }
const item = { name: 'item' }

describe('isItemContentChange', () => {
  it.each`
    target       | expected | case
    ${item}      | ${true}  | ${'a change inside an item'}
    ${container} | ${false} | ${'items shown or hidden by the hook'}
  `('returns $expected for $case', ({ expected, target }) => {
    expect(isItemContentChange({ target }, container)).toBe(expected)
  })
})
