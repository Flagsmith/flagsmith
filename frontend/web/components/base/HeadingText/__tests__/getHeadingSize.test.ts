import { getHeadingSize } from 'components/base/HeadingText/headingSize'

describe('getHeadingSize', () => {
  it.each([
    [1, 'lg'],
    [2, 'md'],
    [3, 'sm'],
    [4, 'sm'],
    [5, 'sm'],
    [6, 'sm'],
  ] as const)('level %i is %s', (level, size) => {
    expect(getHeadingSize(level)).toBe(size)
  })
})
