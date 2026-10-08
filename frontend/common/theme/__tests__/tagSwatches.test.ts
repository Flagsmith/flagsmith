import { contentColours } from 'common/theme/tokens'
import { contrastRatio } from 'common/theme/contrast'
import { perceptualDistance } from 'common/theme/colourDistance'
import tokens from 'common/theme/tokens.json'

// The chip the dot sits on. A tag is a neutral chip in both themes, so one
// dot colour has to read on both of these.
const CHIP = tokens.color.surface.subtle

// Non-text contrast, WCAG 1.4.11. The dot is the only thing carrying the hue,
// so it is held to it even though the label repeats what it says.
const NON_TEXT = 3

// Below this two dots read as the same colour. 0.10 is the comfortable target;
// the floor is lower because eleven hues do not fit comfortably, which is the
// open question on the palette rather than a licence to crowd it further.
const MIN_DISTANCE = 0.05

const swatches = Object.entries(contentColours)

describe('tag dots', () => {
  // Or everything below runs against nothing and still passes.
  it('finds swatches', () => {
    expect(swatches.length).toBeGreaterThan(0)
  })

  it.each([
    ['light', CHIP.light],
    ['dark', CHIP.dark],
  ])('clears non-text contrast on the %s chip', (_theme, ground) => {
    const failing = swatches
      // Negated rather than `<`: an unparseable hex gives NaN, and NaN is not
      // less than anything, so a typo would pass this instead of failing it.
      .filter(([, hex]) => !(contrastRatio(hex, ground) >= NON_TEXT))
      .map(
        ([name, hex]) => `${name} ${contrastRatio(hex, ground).toFixed(2)}:1`,
      )
    expect(failing).toEqual([])
  })

  it('keeps every pair of hues far enough apart to tell apart', () => {
    const tooClose = swatches
      .flatMap(([aName, a], i) =>
        swatches.slice(i + 1).map(([bName, b]) => ({
          distance: perceptualDistance(a, b),
          pair: `${aName}/${bName}`,
        })),
      )
      .filter(({ distance }) => !(distance >= MIN_DISTANCE))
      .map(({ distance, pair }) => `${pair} ${distance.toFixed(3)}`)
    expect(tooClose).toEqual([])
  })

  it('gives every hue a distinct colour', () => {
    const seen = new Set(swatches.map(([, hex]) => hex.toLowerCase()))
    expect(seen.size).toBe(swatches.length)
  })
})
