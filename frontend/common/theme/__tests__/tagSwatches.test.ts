import tokens from 'common/theme/tokens.json'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

const primitives = tokens.primitives as Record<string, string>

const INK = primitives['content-always-dark']

const swatches = Object.entries(primitives).filter(
  ([name, hex]) => name.startsWith('content-') && hex !== INK,
)

const ratio = (hex: string) => contrastRatio(INK, hex)

describe('tag swatches', () => {
  // Or everything below runs against nothing and still passes.
  it('finds swatches', () => {
    expect(swatches.length).toBeGreaterThan(0)
  })

  // One fill on both themes, so the palette settles the label's contrast. The
  // fill is 1.18:1 against white, under the 3:1 for non-text, by design: a tag
  // is read from its label, not its edge.
  it('clears AA for the label on every fill', () => {
    const failing = swatches
      .filter(([, hex]) => ratio(hex) < AA_NORMAL_TEXT)
      .map(([name, hex]) => `${name} ${ratio(hex).toFixed(2)}:1`)
    expect(failing).toEqual([])
  })

  // #8465 found 20 options resolving to 7 colours. Two tags that look alike is
  // the same defect as failing contrast.
  it('gives every hue a distinct colour', () => {
    const seen = new Set(swatches.map(([, hex]) => hex.toLowerCase()))
    expect(seen.size).toBe(swatches.length)
  })
})
