import tokens from 'common/theme/tokens.json'
import {
  AA_NON_TEXT,
  AA_NORMAL_TEXT,
  contrastRatio,
} from 'common/theme/contrast'

const primitives = tokens.primitives as Record<string, string>

const swatches = Object.entries(primitives).filter(([name]) =>
  name.startsWith('content-'),
)

// One stored colour per tag, doing a different job on each ground: a fill
// under this ink in light, the border against this page in dark.
const LIGHT_INK = primitives['slate-600']
const DARK_PAGE = primitives['slate-950']

describe('tag swatches', () => {
  it('has a colour for every hue', () => {
    expect(swatches.length).toBeGreaterThan(0)
  })

  describe.each(swatches)('%s', (_name, colour) => {
    it('passes AA for the label on the fill, in light', () => {
      expect(contrastRatio(LIGHT_INK, colour)).toBeGreaterThanOrEqual(
        AA_NORMAL_TEXT,
      )
    })

    // In dark there is no fill and the label takes the page's own ink, so the
    // border is what has to carry the hue. Non-text, hence 3:1.
    it('passes non-text contrast as the border against the dark page', () => {
      expect(contrastRatio(colour, DARK_PAGE)).toBeGreaterThanOrEqual(
        AA_NON_TEXT,
      )
    })
  })

  // Tags are told apart by colour alone, so two rendering alike is the same
  // defect as failing contrast: #8465 found 20 options resolving to 7 colours.
  it('gives every hue a distinct colour', () => {
    const values = swatches.map(([, hex]) => hex.toLowerCase())
    expect(new Set(values).size).toBe(values.length)
  })
})
