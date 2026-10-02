import { contentColours } from 'common/theme/tokens'
import { getTagSwatch, getTagSwatchUtilities } from './..'

describe('getTagSwatch', () => {
  // What the picker stores now, so this is the common path.
  it.each(Object.entries(contentColours))('knows its own %s', (name, hex) => {
    expect(getTagSwatch(hex)).toBe(name)
  })

  // The colours the picker used to offer, and the ones the app still assigns
  // itself. These are what existing tags hold.
  it.each([
    ['#3d4db6', 'blue'],
    ['#344562', 'blue'],
    ['#5d6d7e', 'blue'],
    ['#ea5a45', 'light-brown'],
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

  // A colour we never issued gets the neutral, not a guess.
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

  it('falls back to neutral utilities when there is no swatch', () => {
    expect(getTagSwatchUtilities('#123456')).toBe(
      'bg-surface-subtle text-default',
    )
    expect(getTagSwatchUtilities('#1492f4')).toBe('tag-blue')
  })
})
