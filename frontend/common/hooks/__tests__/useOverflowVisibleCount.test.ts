import { getMeasureReason } from 'common/hooks/useOverflowVisibleCount'

const itemsContainer = { name: 'container' }
const item = { name: 'item' }

describe('getMeasureReason', () => {
  it.each`
    changedNodes              | isOverflowing | overflowChecked | shownCount | expected      | case
    ${[item]}                 | ${false}      | ${false}        | ${3}       | ${'content'}  | ${'a change inside an item'}
    ${[item]}                 | ${true}       | ${true}         | ${3}       | ${'content'}  | ${'a change inside an item after an overflow check'}
    ${[itemsContainer]}       | ${false}      | ${false}        | ${3}       | ${undefined}  | ${'items shown or hidden that fit'}
    ${[itemsContainer]}       | ${true}       | ${false}        | ${3}       | ${'overflow'} | ${'a shown item that no longer fits'}
    ${[itemsContainer]}       | ${true}       | ${true}         | ${3}       | ${undefined}  | ${'an overflow already checked'}
    ${[itemsContainer]}       | ${true}       | ${false}        | ${0}       | ${undefined}  | ${'only the menu button overflowing'}
    ${[itemsContainer, item]} | ${false}      | ${false}        | ${3}       | ${'content'}  | ${'a mix including an item change'}
  `(
    'returns $expected for $case',
    ({
      changedNodes,
      expected,
      isOverflowing,
      overflowChecked,
      shownCount,
    }) => {
      expect(
        getMeasureReason({
          changedNodes,
          isOverflowing,
          itemsContainer,
          overflowChecked,
          shownCount,
        }),
      ).toBe(expected)
    },
  )
})
