import { contentColours } from 'common/theme/tokens'
import { getTagSwatch } from './..'
import { chipColourClass } from 'components/base/Chip/chipColour'

describe('getTagSwatch', () => {
  it.each(Object.entries(contentColours))('knows its own %s', (name, hex) => {
    expect(getTagSwatch(hex)).toBe(name)
  })

  // The colours the picker used to offer, and the ones the app still assigns
  // itself. These are what existing tags hold.
  it.each([
    ['#3d4db6', 'blue'],
    ['#344562', 'light-grey'],
    ['#5d6d7e', 'light-grey'],
    ['#ea5a45', 'light-red'],
    ['#641e16', 'light-brown'],
    ['#ffa500', 'light-peach'],
    ['#d35400', 'light-peach'],
    ['#aac200', 'light-yellow'],
    ['#3cb371', 'light-green'],
    ['#dedede', 'light-grey'],
    ['#8f8f8f', 'light-grey'],
  ])('maps the legacy %s', (colour, expected) => {
    expect(getTagSwatch(colour)).toBe(expected)
  })

  it('is case-insensitive', () => {
    expect(getTagSwatch('#1492F4')).toBe('blue')
  })

  it.each([
    undefined,
    null,
    '',
    'rebeccapurple',
    '#123456',
    // Would find an inherited property if the map were an object literal.
    'constructor',
    '__proto__',
  ])('has no swatch for %s', (colour) => {
    expect(getTagSwatch(colour)).toBeNull()
  })

  it('maps a legacy colour to its swatch class', () => {
    const swatch = getTagSwatch('#1492f4')
    expect(swatch).toBe('blue')
    expect(swatch && chipColourClass(swatch)).toBe('tag-blue')
  })
})
