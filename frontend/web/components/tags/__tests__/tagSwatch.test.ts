import { contentColours } from 'common/theme/tokens'
import { getTagSwatch, getTagSwatchUtilities } from 'components/tags/tagSwatch'

// Constants.tagColors, inlined: importing common/constants pulls in the Flux
// dispatcher, which wants a `window` this node-environment suite has not got.
const PICKER_COLOURS = [
  '#1492f4',
  '#14c0f4',
  '#d3d3d3',
  '#039587',
  '#c6b215',
  '#d35400',
  '#f08080',
  '#de3163',
  '#c277e0',
  '#641e16',
  '#60bd4e',
]

describe('getTagSwatch', () => {
  // The picker offers one colour per Content swatch, so two tags picked apart
  // in the list never come out the same. #8465 found the old 20 collapsing to
  // 7 once contrast was applied.
  it('maps the picker one-to-one onto the Content colours', () => {
    const swatches = PICKER_COLOURS.map(getTagSwatch)
    expect(new Set(swatches).size).toBe(PICKER_COLOURS.length)
    expect(new Set(swatches)).toEqual(new Set(Object.keys(contentColours)))
  })

  // Colours the picker never offered still have to render as tags: `color` is
  // a bare CharField, so the API and imports can store anything.
  it.each([
    ['#3d4db6', 'blue'],
    ['#5b2c6f', 'light-purple'],
    ['#ea5a45', 'light-brown'],
    ['#ffa500', 'light-peach'],
    ['#aac200', 'light-yellow'],
    ['#3cb371', 'light-green'],
  ])('matches %s on hue', (colour, expected) => {
    expect(getTagSwatch(colour)).toBe(expected)
  })

  it('sends greys to the grey swatch', () => {
    expect(getTagSwatch('#d3d3d3')).toBe('light-grey')
    // Constants.untaggedTag
    expect(getTagSwatch('#dedede')).toBe('light-grey')
  })

  it('is case-insensitive', () => {
    expect(getTagSwatch('#1492F4')).toBe('blue')
  })

  it.each([undefined, null, '', 'rebeccapurple', '#fff'])(
    'has no swatch for %s',
    (colour) => {
      expect(getTagSwatch(colour)).toBeNull()
    },
  )

  it('falls back to neutral utilities when there is no swatch', () => {
    expect(getTagSwatchUtilities('rebeccapurple')).toBe(
      'bg-surface-subtle text-default',
    )
    expect(getTagSwatchUtilities('#1492f4')).toBe('tag-blue')
  })
})
