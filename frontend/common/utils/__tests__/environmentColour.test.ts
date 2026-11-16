import { getEnvironmentColour } from 'common/utils/environmentColour'
import { TAG_COLOURS } from 'common/theme/tagColours'

describe('getEnvironmentColour', () => {
  it('uses the banner colour when the environment has one', () => {
    expect(getEnvironmentColour({ banner_colour: '#123456' }, 3)).toBe(
      '#123456',
    )
  })

  it.each`
    name                  | environment
    ${'no banner colour'} | ${{}}
    ${'an empty colour'}  | ${{ banner_colour: '' }}
    ${'a null colour'}    | ${{ banner_colour: null }}
  `('falls back to the position colour with $name', ({ environment }) => {
    expect(getEnvironmentColour(environment, 1)).toBe(TAG_COLOURS[1])
  })

  it('wraps the position the same way Utils.getTagColour does', () => {
    expect(getEnvironmentColour({}, TAG_COLOURS.length - 1)).toBe(
      TAG_COLOURS[0],
    )
  })
})
