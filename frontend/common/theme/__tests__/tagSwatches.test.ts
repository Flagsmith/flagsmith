import tokens from 'common/theme/tokens.json'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

const primitives = tokens.primitives as Record<string, string>

// The ink every tag's label takes, on either theme.
const INK = primitives['content-always-dark']

const swatches = Object.entries(primitives).filter(
  ([name, hex]) => name.startsWith('content-') && hex !== INK,
)

// A tag keeps one fill on both themes, so the label's contrast is fixed by the
// palette and cannot change with the page. The fill itself sits at 1.18:1
// against white, well under the 3:1 for non-text: that is by design, since a
// tag is read from its label rather than from its edge.
describe('tag swatches', () => {
  it('has a colour for every hue', () => {
    expect(swatches.length).toBeGreaterThan(0)
  })

  describe.each(swatches)('%s', (_name, colour) => {
    it('passes AA for the label on the fill', () => {
      expect(contrastRatio(INK, colour)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT)
    })
  })

  // Tags are told apart by colour alone, so two rendering alike is the same
  // defect as failing contrast: #8465 found 20 options resolving to 7 colours.
  it('gives every hue a distinct colour', () => {
    const values = swatches.map(([, hex]) => hex.toLowerCase())
    expect(new Set(values).size).toBe(values.length)
  })
})
