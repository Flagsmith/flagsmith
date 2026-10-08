import Color from 'color'
import tokens from './tokens.json'
import { relativeLuminance } from './contrast'

// A tag's colour is a hex the user picked, or one set through the API, so it
// can be any colour at all. Drawn as a dot it has to read on the chip it sits
// on, in both themes, and the chip is the same neutral one in each. That gives
// one window of luminance a dot has to land in.
const CHIP = tokens.color.surface.subtle

// Inside the 3:1 window rather than on its edge: a hex is 8-bit, and a value
// placed exactly on the boundary rounds to just under it.
const TARGET_RATIO = 3.2

const windowFor = (lighterGround: string, darkerGround: string) => ({
  // Dark enough to read on the light chip.
  max: (relativeLuminance(lighterGround) + 0.05) / TARGET_RATIO - 0.05,
  // Light enough to read on the dark chip.
  min: TARGET_RATIO * (relativeLuminance(darkerGround) + 0.05) - 0.05,
})

const WINDOW = windowFor(CHIP.light, CHIP.dark)

// Luminance rises with lightness whatever the hue, so the value that hits a
// target can be found by halving the interval. Doing it on measured luminance
// rather than on a lightness figure is the point: lightness is not luminance,
// and the gap is widest exactly where it matters, on blues and purples.
const STEPS = 20

const atLuminance = (colour: Color, target: number): string => {
  const [hue, saturation] = [colour.hue(), colour.saturationl()]
  let low = 0
  let high = 100
  for (let i = 0; i < STEPS; i += 1) {
    const mid = (low + high) / 2
    const candidate = Color.hsl(hue, saturation, mid).hex()
    if (relativeLuminance(candidate) < target) low = mid
    else high = mid
  }
  return Color.hsl(hue, saturation, high).hex().toLowerCase()
}

/**
 * The given colour, moved to the nearest lightness at which it reads as a dot
 * on a tag in either theme. Hue and saturation are untouched, so the colour is
 * still recognisably the one that was chosen.
 */
export const dotColour = (colour: string): string => {
  const parsed = Color(colour)
  const luminance = relativeLuminance(parsed.hex())
  if (luminance >= WINDOW.min && luminance <= WINDOW.max) {
    return parsed.hex().toLowerCase()
  }
  return atLuminance(parsed, luminance < WINDOW.min ? WINDOW.min : WINDOW.max)
}
