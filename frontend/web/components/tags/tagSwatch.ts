import { contentColourNames, contentColours } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'

/** One swatch per Content hue, named as the design system names it. */
export type TagSwatch = ContentColour

// Existing tags to the palette that replaced them (#8465): Constants.tagColors
// plus the archived and untagged pseudo-tags. Anything else gets the neutral.
const LEGACY_BY_COLOR: Record<string, TagSwatch> = {
  '#039587': 'light-mint',
  '#1492f4': 'blue',
  '#14c0f4': 'light-blue',
  '#344562': 'blue',
  '#3cb371': 'light-green',
  '#3d4db6': 'blue',
  '#5b2c6f': 'light-purple',
  '#5d6d7e': 'blue',
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
  '#ea5a45': 'light-brown',
  '#f08080': 'light-red',
  '#fe5505': 'light-peach',
  '#ffa500': 'light-peach',
}

const PALETTE_BY_COLOR: Record<string, TagSwatch> = Object.fromEntries(
  contentColourNames.map((name) => [contentColours[name], name]),
)

export const getTagSwatch = (color?: string | null): TagSwatch | null => {
  if (!color) return null
  const key = color.toLowerCase()
  // The picker stores the palette's own value, so the legacy map is a fallback.
  return PALETTE_BY_COLOR[key] ?? LEGACY_BY_COLOR[key] ?? null
}

/** "light-green" reads as "Light green": a swatch has no other name. */
export const swatchLabel = (swatch: TagSwatch): string => {
  const words = swatch.replace(/-/g, ' ')
  return words[0].toUpperCase() + words.slice(1)
}

/** The generator emits one of these per Content hue. */
export const swatchUtilities = (swatch: TagSwatch): string => `tag-${swatch}`

// A colour we never issued, so no swatch is a better answer than a guess.
const NEUTRAL_UTILITIES = 'bg-surface-subtle text-default'

export const getTagSwatchUtilities = (color?: string | null): string => {
  const swatch = getTagSwatch(color)
  return swatch ? swatchUtilities(swatch) : NEUTRAL_UTILITIES
}
