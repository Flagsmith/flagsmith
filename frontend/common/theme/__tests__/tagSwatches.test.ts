import {
  contentColourNames,
  contentColours,
  contentColoursDark,
  contentInk,
} from 'common/theme/tokens'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

// A tag is a fill and an ink, and the two swap roles between the themes: in
// light the ink is shared, in dark it is the light fill over a deep one.
const THEMES = ['light', 'dark'] as const

const PAIRINGS = {
  dark: (name: (typeof contentColourNames)[number]) => ({
    fill: contentColoursDark[name],
    ink: contentColours[name],
  }),
  light: (name: (typeof contentColourNames)[number]) => ({
    fill: contentColours[name],
    ink: contentInk,
  }),
}

describe('tag swatches', () => {
  // Or everything below runs against nothing and still passes.
  it('finds swatches', () => {
    expect(contentColourNames.length).toBeGreaterThan(0)
  })

  it.each(THEMES)('clears AA for the label on every %s fill', (theme) => {
    const failing = contentColourNames
      .map((name) => ({ name, ...PAIRINGS[theme](name) }))
      .map(({ fill, ink, name }) => ({
        name,
        ratio: contrastRatio(ink, fill),
      }))
      // Negated rather than `<`: an unparseable hex gives NaN, and NaN
      // is not less than anything, so a typo would pass, not fail.
      .filter(({ ratio }) => !(ratio >= AA_NORMAL_TEXT))
      .map(({ name, ratio }) => `${name} ${ratio.toFixed(2)}:1`)
    expect(failing).toEqual([])
  })

  it.each(THEMES)('gives every hue a distinct %s fill', (theme) => {
    const fills = contentColourNames.map((name) =>
      PAIRINGS[theme](name).fill.toLowerCase(),
    )
    expect(new Set(fills).size).toBe(fills.length)
  })
})
