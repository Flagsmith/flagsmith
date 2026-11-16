import {
  getEnvironmentColour,
  getEnvironmentColourById,
} from 'common/utils/environmentColour'
import { TAG_COLOURS } from 'common/theme/tagColours'

describe('getEnvironmentColour', () => {
  it('uses the banner colour when the environment has one', () => {
    expect(getEnvironmentColour({ banner_colour: '#123456' }, 3)).toBe(
      '#123456',
    )
  })

  it.each`
    name                   | environment
    ${'no banner colour'}  | ${{}}
    ${'an empty colour'}   | ${{ banner_colour: '' }}
    ${'a null colour'}     | ${{ banner_colour: null }}
    ${'an invalid colour'} | ${{ banner_colour: 'red' }}
  `('falls back to the position colour with $name', ({ environment }) => {
    expect(getEnvironmentColour(environment, 1)).toBe(TAG_COLOURS[1])
  })

  it('wraps the position the same way Utils.getTagColour does', () => {
    expect(getEnvironmentColour({}, TAG_COLOURS.length - 1)).toBe(
      TAG_COLOURS[0],
    )
  })

  it('adds the # to a banner colour stored without it', () => {
    expect(getEnvironmentColour({ banner_colour: ' 123456 ' }, 0)).toBe(
      '#123456',
    )
  })
})

describe('getEnvironmentColourById', () => {
  const environments = [
    { banner_colour: '#111111', id: 1 },
    { banner_colour: null, id: 2 },
  ]

  it('uses the banner colour of the matching environment', () => {
    expect(getEnvironmentColourById(environments, '1')).toBe('#111111')
  })

  it('uses the position colour when it has none', () => {
    expect(getEnvironmentColourById(environments, 2)).toBe(TAG_COLOURS[1])
  })

  it("never borrows another environment's banner colour", () => {
    expect(getEnvironmentColourById(environments, 99)).toBe(TAG_COLOURS[0])
  })
})
