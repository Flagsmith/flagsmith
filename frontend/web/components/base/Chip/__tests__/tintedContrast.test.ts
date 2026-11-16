import { readFileSync } from 'fs'
import { resolve } from 'path'
import tokens from 'common/theme/tokens.json'
import { TAG_COLOURS } from 'common/theme/tagColours'

// Read from the shipped styles, so changing them can't skip this check.
const stylesheet = (path: string) =>
  readFileSync(resolve(__dirname, path), 'utf8')
const percentages = (css: string, pattern: RegExp) =>
  [...css.matchAll(pattern)].map((match) => Number(match[1]) / 100)

const chipScss = stylesheet('../Chip.scss')
const [TEXT_STRENGTH] = percentages(
  chipScss,
  /var\(--chip-colour\) (\d+)%, var\(--color-text-default\)/g,
)
const TINTS = [
  ...percentages(chipScss, /--chip-tint: (\d+)%/g),
  ...percentages(
    stylesheet('../../ToggleChip/ToggleChip.scss'),
    /--chip-tint: (\d+)%/g,
  ),
]
const THEMES: ('light' | 'dark')[] = ['light', 'dark']

type Rgb = [number, number, number]
const rgb = (hex: string): Rgb => {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
const mix = (a: Rgb, b: Rgb, amountOfA: number): Rgb => [
  a[0] * amountOfA + b[0] * (1 - amountOfA),
  a[1] * amountOfA + b[1] * (1 - amountOfA),
  a[2] * amountOfA + b[2] * (1 - amountOfA),
]
const channel = (v: number) => {
  const s = v / 255
  return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
}
const luminance = ([r, g, b]: Rgb) =>
  0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
const contrast = (a: Rgb, b: Rgb) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

// The tag palette plus the extremes; white is the worst case (4.88:1).
const COLOURS = [
  ...TAG_COLOURS,
  '#ffffff',
  '#000000',
  '#f5e1a4',
  '#1a1a2e',
  '#ffff00',
]

describe('tinted chip text', () => {
  it('finds the text mix and both tints in the styles', () => {
    expect(TEXT_STRENGTH).toBeGreaterThan(0)
    expect(TINTS).toHaveLength(2)
  })

  it.each(COLOURS)('%s reads at 4.5:1 in both themes and tints', (hex) => {
    const colour = rgb(hex)
    for (const theme of THEMES) {
      const surface = rgb(tokens.color.surface.default[theme])
      const text = mix(
        colour,
        rgb(tokens.color.text.default[theme]),
        TEXT_STRENGTH,
      )
      for (const tint of TINTS) {
        expect(
          contrast(text, mix(colour, surface, tint)),
        ).toBeGreaterThanOrEqual(4.5)
      }
    }
  })
})
