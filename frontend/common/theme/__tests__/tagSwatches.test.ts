import tokens from 'common/theme/tokens.json'
import { AA_NORMAL_TEXT, contrastRatio } from 'common/theme/contrast'

type Entry = { cssVar: string; light: string; dark: string }

const surfaces = tokens.tag.surface as Record<string, Entry>
const texts = tokens.tag.text as Record<string, Entry>
const primitives = tokens.primitives as Record<string, string>

const hues = Object.keys(surfaces)

describe('tag swatches', () => {
  it('defines a surface and a text token for every hue', () => {
    expect(hues.length).toBeGreaterThan(0)
    expect(Object.keys(texts)).toEqual(hues)
  })

  describe.each(hues)('%s', (hue) => {
    const surface = surfaces[hue]
    const text = texts[hue]

    it.each(['light', 'dark'] as const)('passes AA in %s mode', (theme) => {
      expect(contrastRatio(surface[theme], text[theme])).toBeGreaterThanOrEqual(
        AA_NORMAL_TEXT,
      )
    })
  })

  // Tags are told apart by colour alone, so two swatches rendering alike is
  // the same defect as failing contrast: #8465 found the picker offering 20
  // options that resolved to 7 colours.
  it.each(['light', 'dark'] as const)(
    'gives every swatch a distinct surface in %s mode',
    (theme) => {
      const fills = hues.map((hue) => surfaces[hue][theme].toLowerCase())
      expect(new Set(fills).size).toBe(fills.length)
    },
  )
})
