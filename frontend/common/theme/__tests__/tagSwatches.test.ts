import tokens from 'common/theme/tokens.json'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

const primitives = tokens.primitives as Record<string, string>

const swatches = Object.entries(primitives).filter(([name]) =>
  name.startsWith('content-'),
)

// Every tag chip uses this one ink. The Content colours are fixed rather than
// theme-aware, because a chip carries its own surface and does not follow the
// page, so one ink has to work on all of them in both themes.
const TAG_INK = primitives['slate-600']

describe('tag swatches', () => {
  it('has a swatch for every Content colour', () => {
    expect(swatches.length).toBeGreaterThan(0)
  })

  describe.each(swatches)('%s', (_name, fill) => {
    it('passes AA against the tag ink', () => {
      expect(contrastRatio(fill, TAG_INK)).toBeGreaterThanOrEqual(
        AA_NORMAL_TEXT,
      )
    })
  })

  // Tags are told apart by colour alone, so two swatches rendering alike is
  // the same defect as failing contrast: #8465 found the picker offering 20
  // options that resolved to 7 colours.
  it('gives every swatch a distinct fill', () => {
    const fills = swatches.map(([, hex]) => hex.toLowerCase())
    expect(new Set(fills).size).toBe(fills.length)
  })
})
