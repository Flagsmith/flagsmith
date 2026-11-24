import { shouldMeasureAgain } from 'common/hooks/useOverflowVisibleCount'

const itemsContainer = { name: 'container' }
const item = { name: 'item' }

describe('shouldMeasureAgain', () => {
  it.each`
    changedNodes              | isOverflowing | shownCount | expected | case
    ${[item]}                 | ${false}      | ${3}       | ${true}  | ${'a change inside an item'}
    ${[itemsContainer]}       | ${false}      | ${3}       | ${false} | ${'items shown or hidden that fit'}
    ${[itemsContainer]}       | ${true}       | ${3}       | ${true}  | ${'a shown item that no longer fits'}
    ${[itemsContainer]}       | ${true}       | ${0}       | ${false} | ${'only the menu button overflowing'}
    ${[itemsContainer, item]} | ${false}      | ${3}       | ${true}  | ${'a mix including an item change'}
  `(
    'returns $expected for $case',
    ({ changedNodes, expected, isOverflowing, shownCount }) => {
      expect(
        shouldMeasureAgain({
          changedNodes,
          isOverflowing,
          itemsContainer,
          shownCount,
        }),
      ).toBe(expected)
    },
  )
})
