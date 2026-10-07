import tokens from 'common/theme/tokens.json'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

const THEMES = ['light', 'dark'] as const

type Slot = Record<string, { dark: string; light: string }>
const BG: Slot = tokens.contentBg
const TEXT: Slot = tokens.contentText

// Dark grounds on the lightest surface a tag can land on rather than the page,
// since an outlined tag lets whatever is behind it show through.
const groundFor = (hue: string, theme: (typeof THEMES)[number]) =>
  theme === 'light' ? BG[hue].light : tokens.primitives['slate-800']

describe('tag swatches', () => {
  // Or everything below runs against nothing and still passes.
  it('finds swatches', () => {
    expect(Object.keys(BG).length).toBeGreaterThan(0)
  })

  it.each(THEMES)('clears AA for the label in %s', (theme) => {
    const failing = Object.keys(BG)
      .map((hue) => ({
        hue,
        // The token that paints the label, not a value that happens to match it.
        ratio: contrastRatio(TEXT[hue][theme], groundFor(hue, theme)),
      }))
      // Negated rather than `<`: an unparseable hex gives NaN, and NaN is
      // not less than anything, so a typo would pass, not fail.
      .filter(({ ratio }) => !(ratio >= AA_NORMAL_TEXT))
      .map(({ hue, ratio }) => `${hue} ${ratio.toFixed(2)}:1`)
    expect(failing).toEqual([])
  })

  it('gives every hue a distinct tint', () => {
    const tints = Object.keys(BG).map((hue) => BG[hue].light.toLowerCase())
    expect(new Set(tints).size).toBe(tints.length)
  })
})
