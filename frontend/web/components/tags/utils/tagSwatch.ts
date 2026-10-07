import { contentColourNames, contentColours } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'

type TagSwatch = ContentColour

// Existing tags to the palette that replaced them (#8465): Constants.tagColors
// plus the archived and untagged pseudo-tags.
const LEGACY_COLOURS: Record<string, TagSwatch> = {
  '#039587': 'light-mint',
  '#1492f4': 'blue',
  '#14c0f4': 'light-blue',
  // Navy and slate carry a hue but never showed one: both were drawn as an 8%
  // wash, so what a user has always seen is grey.
  '#344562': 'light-grey',
  '#3cb371': 'light-green',
  '#3d4db6': 'blue',
  '#5b2c6f': 'light-purple',
  '#5d6d7e': 'light-grey',
  '#60bd4e': 'light-green',
  '#641e16': 'light-brown',
  '#8f8f8f': 'light-grey',
  '#aac200': 'light-yellow',
  '#c277e0': 'light-purple',
  '#c6b215': 'light-yellow',
  '#d35400': 'light-peach',
  '#d3d3d3': 'light-grey',
  '#de3163': 'light-pink',
  '#dedede': 'light-grey',
  // Coral is a red, not a brown. light-brown is 3deg closer in hue but 72
  // points less saturated, so it reads as neither.
  '#ea5a45': 'light-red',
  '#f08080': 'light-red',
  '#fe5505': 'light-peach',
  '#ffa500': 'light-peach',
}

// A Map, not an object: a colour named "constructor" would otherwise find an
// inherited property and hand back something that is not a swatch.
const SWATCH_BY_COLOR = new Map<string, TagSwatch>([
  ...Object.entries(LEGACY_COLOURS),
  ...contentColourNames.map((name): [string, TagSwatch] => [
    contentColours[name],
    name,
  ]),
])

export const getTagSwatch = (color?: string | null): TagSwatch | null =>
  (color && SWATCH_BY_COLOR.get(color.toLowerCase())) || null

const swatchLabel = (swatch: TagSwatch): string => {
  const words = swatch.replace(/-/g, ' ')
  return words[0].toUpperCase() + words.slice(1)
}

export const swatchName = (colour?: string | null) => {
  const swatch = getTagSwatch(colour)
  return swatch ? swatchLabel(swatch) : 'Custom colour'
}
