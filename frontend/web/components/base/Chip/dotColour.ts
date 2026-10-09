import Color from 'color'
import tokens from 'common/theme/tokens.json'

// A chip's dot is often a colour from a record rather than from the palette,
// so it can be any colour at all, including one too pale or too dark to see.
// The chip is the same neutral surface in both themes, which gives one window
// of luminance that a dot has to land in to read on either.
const CHIP = tokens.color.surface.subtle

// WCAG 1.4.11, non-text contrast. Aimed at slightly inside the window rather
// than at its edge: a hex is 8-bit, and a value placed exactly on 3:1 rounds
// to just under it.
const TARGET_RATIO = 3.2

const luminanceFor = (ratio: number, against: string) =>
  ratio * (Color(against).luminosity() + 0.05) - 0.05

const WINDOW = {
  // Dark enough to read on the light chip.
  max: (Color(CHIP.light).luminosity() + 0.05) / TARGET_RATIO - 0.05,

  // Light enough to read on the dark chip.
  min: luminanceFor(TARGET_RATIO, CHIP.dark),
}

// Luminance rises with lightness whatever the hue, so the lightness that hits
// a given luminance can be found by halving the interval. Searching on
// luminance rather than on lightness is the point: they are not the same
// measure, and they diverge most on the blues and purples this has to get
// right.
const STEPS = 20

const atLuminance = (colour: Color, target: number): string => {
  const [hue, saturation] = [colour.hue(), colour.saturationl()]
  let low = 0
  let high = 100
  for (let i = 0; i < STEPS; i += 1) {
    const mid = (low + high) / 2
    if (Color.hsl(hue, saturation, mid).luminosity() < target) low = mid
    else high = mid
  }
  return Color.hsl(hue, saturation, high).hex().toLowerCase()
}

/**
 * The given colour, moved to the nearest lightness at which it reads as a dot
 * on a chip in either theme. Hue and saturation are kept, so it is still
 * recognisably the colour that was chosen.
 */
export const dotColour = (colour: string): string => {
  const parsed = Color(colour)
  const luminosity = parsed.luminosity()
  if (luminosity >= WINDOW.min && luminosity <= WINDOW.max) {
    return parsed.hex().toLowerCase()
  }
  return atLuminance(parsed, luminosity < WINDOW.min ? WINDOW.min : WINDOW.max)
}
