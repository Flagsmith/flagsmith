import Color from 'color'
import tokens from 'common/theme/tokens.json'
import { AA_NON_TEXT, contrastRatio } from 'common/theme/contrast'
import { dotColour } from 'common/theme/dotColour'

// Inlined rather than imported: Constants pulls in the dispatcher and the
// stores, and this needs none of them. Source of truth: Constants.tagColors.
const TAG_COLOURS = [
  '#3d4db6',
  '#ea5a45',
  '#c6b215',
  '#60bd4e',
  '#fe5505',
  '#1492f4',
  '#14c0f4',
  '#c277e0',
  '#039587',
  '#344562',
  '#ffa500',
  '#3cb371',
  '#d3d3d3',
  '#5D6D7E',
  '#641E16',
  '#5B2C6F',
  '#D35400',
  '#F08080',
  '#AAC200',
  '#DE3163',
]

const CHIP = tokens.color.surface.subtle
const GROUNDS: [string, string][] = [
  ['light', CHIP.light],
  ['dark', CHIP.dark],
]

// Any colour the API will accept, not just the ones the picker offers.
const arbitrary = (count: number): string[] => {
  let seed = 20_251_008
  return Array.from({ length: count }, () => {
    seed = (seed * 1_103_515_245 + 12_345) % 2 ** 31
    return `#${(seed % 0xffffff).toString(16).padStart(6, '0')}`
  })
}

describe('dotColour', () => {
  // Or everything below runs against nothing and still passes.
  it('finds the palette', () => {
    expect(TAG_COLOURS.length).toBeGreaterThan(0)
  })

  describe.each(GROUNDS)('on the %s chip', (_theme, ground) => {
    it('clears non-text contrast for every colour in the picker', () => {
      const failing = TAG_COLOURS.map((colour) => [colour, dotColour(colour)])
        // Negated rather than `<`: an unparseable hex gives NaN, and NaN is
        // not less than anything, so a typo would pass this instead of
        // failing it.
        .filter(([, dot]) => !(contrastRatio(dot, ground) >= AA_NON_TEXT))
        .map(
          ([colour, dot]) =>
            `${colour} -> ${dot} ${contrastRatio(dot, ground).toFixed(2)}:1`,
        )
      expect(failing).toEqual([])
    })

    it('clears non-text contrast for a colour set through the API', () => {
      const failing = arbitrary(2000)
        .map((colour) => [colour, dotColour(colour)])
        .filter(([, dot]) => !(contrastRatio(dot, ground) >= AA_NON_TEXT))
        .map(([colour, dot]) => `${colour} -> ${dot}`)
      expect(failing).toEqual([])
    })
  })

  it('keeps the hue it was given', () => {
    const moved = TAG_COLOURS.map((colour) => [
      Color(colour),
      Color(dotColour(colour)),
    ])
      // Grey has no meaningful hue to keep, and rounding to 8 bits moves what
      // hue it reports by a lot.
      .filter(([before]) => before.saturationl() > 5)
      .filter(([before, after]) => Math.abs(before.hue() - after.hue()) > 2)
      .map(([before, after]) => `${before.hex()} -> ${after.hex()}`)
    expect(moved).toEqual([])
  })

  it('leaves a colour already in the window alone', () => {
    // Mid orange: readable on both chips as it stands.
    expect(dotColour('#d35400')).toBe('#d35400')
  })

  it('lightens a colour too dark for the dark chip', () => {
    expect(Color(dotColour('#641e16')).luminosity()).toBeGreaterThan(
      Color('#641e16').luminosity(),
    )
  })

  it('darkens a colour too light for the light chip', () => {
    expect(Color(dotColour('#d3d3d3')).luminosity()).toBeLessThan(
      Color('#d3d3d3').luminosity(),
    )
  })
})
