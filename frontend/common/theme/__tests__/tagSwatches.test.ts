import { contentColours, contentInk } from 'common/theme/tokens'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

const swatches = Object.entries(contentColours)
const ratio = (hex: string) => contrastRatio(contentInk, hex)

describe('tag swatches', () => {
  // Or everything below runs against nothing and still passes.
  it('finds swatches', () => {
    expect(swatches.length).toBeGreaterThan(0)
  })

  it('clears AA for the label on every fill', () => {
    const failing = swatches
      .filter(([, hex]) => ratio(hex) < AA_NORMAL_TEXT)
      .map(([name, hex]) => `${name} ${ratio(hex).toFixed(2)}:1`)
    expect(failing).toEqual([])
  })

  it('gives every hue a distinct colour', () => {
    const seen = new Set(swatches.map(([, hex]) => hex.toLowerCase()))
    expect(seen.size).toBe(swatches.length)
  })
})
