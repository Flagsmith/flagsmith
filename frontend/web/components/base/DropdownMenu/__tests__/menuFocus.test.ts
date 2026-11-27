import { nextMenuIndex } from 'components/base/DropdownMenu/menuFocus'

describe('nextMenuIndex', () => {
  it.each`
    key            | index | count | expected
    ${'ArrowDown'} | ${0}  | ${3}  | ${1}
    ${'ArrowDown'} | ${2}  | ${3}  | ${0}
    ${'ArrowUp'}   | ${1}  | ${3}  | ${0}
    ${'ArrowUp'}   | ${0}  | ${3}  | ${2}
    ${'ArrowUp'}   | ${-1} | ${3}  | ${2}
    ${'Home'}      | ${2}  | ${3}  | ${0}
    ${'End'}       | ${0}  | ${3}  | ${2}
    ${'Tab'}       | ${0}  | ${3}  | ${null}
  `(
    '$key from $index of $count: $expected',
    ({ count, expected, index, key }) => {
      expect(nextMenuIndex(key, index, count)).toBe(expected)
    },
  )
})
