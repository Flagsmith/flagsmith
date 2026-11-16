import type { CSSProperties } from 'react'
import tokens from 'common/theme/tokens.json'
import { parseHex, Rgb } from 'common/utils/parseHex'

export type ChipTheme = 'light' | 'dark'
// CSS custom properties, typed as styles so they can go on `style`.
export type ChipColourVars = CSSProperties & {
  '--chip-colour': string
  '--chip-text-strength': string
}

// Kept in step with Chip.scss, which mixes the same amounts in CSS.
export const CHIP_TINT = { base: 0.12, selected: 0.22 }
const MIN_TEXT_CONTRAST = 4.5

const themeColour = (
  token: { light: string; dark: string },
  theme: ChipTheme,
) => parseHex(token[theme]) ?? { b: 0, g: 0, r: 0 }

const mix = (a: Rgb, b: Rgb, amountOfA: number): Rgb => ({
  b: a.b * amountOfA + b.b * (1 - amountOfA),
  g: a.g * amountOfA + b.g * (1 - amountOfA),
  r: a.r * amountOfA + b.r * (1 - amountOfA),
})

const channel = (value: number) => {
  const c = value / 255
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
}
const luminance = ({ b, g, r }: Rgb) =>
  0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

export const contrastRatio = (a: Rgb, b: Rgb) => {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

// What Chip.scss renders for a colour in one theme.
export const getChipShades = (
  colour: Rgb,
  theme: ChipTheme,
  textStrength: number,
) => {
  const surface = themeColour(tokens.color.surface.default, theme)
  const textDefault = themeColour(tokens.color.text.default, theme)
  return {
    background: mix(colour, surface, CHIP_TINT.base),
    selectedBackground: mix(colour, surface, CHIP_TINT.selected),
    text: mix(colour, textDefault, textStrength),
  }
}

const readsInBothThemes = (colour: Rgb, textStrength: number) =>
  (['light', 'dark'] as const).every((theme) => {
    const { background, selectedBackground, text } = getChipShades(
      colour,
      theme,
      textStrength,
    )
    return (
      contrastRatio(text, background) >= MIN_TEXT_CONTRAST &&
      contrastRatio(text, selectedBackground) >= MIN_TEXT_CONTRAST
    )
  })

// The most of the colour the text can keep while reading at 4.5:1 in both
// themes; the rest is the theme's default text colour.
export const getChipTextStrength = (colour: Rgb) => {
  for (let step = 50; step > 0; step--) {
    if (readsInBothThemes(colour, step / 50)) return step / 50
  }
  return 0
}

// Returns null for anything that isn't a 6-digit hex, so the chip keeps its
// variant.
export const getChipColourVars = (hex: string): ChipColourVars | null => {
  const colour = parseHex(hex)
  if (!colour) return null
  return {
    '--chip-colour': `#${hex.trim().replace(/^#/, '')}`,
    '--chip-text-strength': `${Math.round(getChipTextStrength(colour) * 100)}%`,
  }
}
