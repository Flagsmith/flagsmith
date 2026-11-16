import {
  contrastRatio,
  getChipColourVars,
  getChipShades,
  getChipTextStrength,
} from 'components/base/Chip/chipColour'
import { parseHex } from 'common/utils/parseHex'
import { TAG_COLOURS } from 'common/theme/tagColours'

const HARD_CASES = ['#f5e1a4', '#1a1a2e', '#ffffff', '#000000', '#ffa500']
const CASES = [...TAG_COLOURS, ...HARD_CASES].flatMap((hex) => [
  { hex, theme: 'light' as const },
  { hex, theme: 'dark' as const },
])

describe('getChipTextStrength', () => {
  it.each(CASES)(
    '$hex in $theme mode reads at 4.5:1 or better',
    ({ hex, theme }) => {
      const colour = parseHex(hex)
      if (!colour) throw new Error(`bad hex ${hex}`)
      // Rounded the same way as the CSS variable.
      const strength = Math.round(getChipTextStrength(colour) * 100) / 100
      const shades = getChipShades(colour, theme, strength)
      expect(
        contrastRatio(shades.text, shades.background),
      ).toBeGreaterThanOrEqual(4.5)
      expect(
        contrastRatio(shades.text, shades.selectedBackground),
      ).toBeGreaterThanOrEqual(4.5)
    },
  )
})

describe('getChipColourVars', () => {
  it('passes the colour and how much of it the text keeps', () => {
    const vars = getChipColourVars('ea5a45')
    expect(vars?.['--chip-colour']).toBe('#ea5a45')
    expect(vars?.['--chip-text-strength']).toMatch(/^\d+%$/)
  })

  it.each(['', 'red', '#abc', '#12345g'])('returns null for %p', (value) => {
    expect(getChipColourVars(value)).toBeNull()
  })
})
