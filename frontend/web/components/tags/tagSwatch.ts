import { Tag as TTag } from 'common/types/responses'
import { contentColours } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'

/** One swatch per Content hue, named as the design system names it. */
export type TagSwatch = ContentColour

// Every colour a tag has been given a way to hold: the twenty the picker used
// to offer, plus the four the app assigns itself. `Tag.color` is an unvalidated
// CharField, so anything else falls through to the neutral below.
const SWATCH_BY_COLOR: Record<string, TagSwatch> = {
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

const BY_SWATCH_VALUE = Object.fromEntries(
  Object.entries(contentColours).map(([name, hex]) => [hex, name as TagSwatch]),
)

export const getTagSwatch = (color?: string | null): TagSwatch | null => {
  if (!color) return null
  const key = color.toLowerCase()
  // The picker stores the swatch itself, so a current tag needs no lookup.
  return BY_SWATCH_VALUE[key] ?? SWATCH_BY_COLOR[key] ?? null
}

// A colour we have never issued, from the API or an import. Neutral rather than
// a guess: the label still reads, and the tag is not claiming a category it was
// not given.
const NEUTRAL_UTILITIES = 'bg-surface-subtle text-default'

export const getTagSwatchUtilities = (color?: string | null): string => {
  const swatch = getTagSwatch(color)
  return swatch ? `tag-${swatch}` : NEUTRAL_UTILITIES
}

export const isSystemTag = (tag: Partial<TTag>): boolean =>
  !!tag.type && tag.type !== 'NONE'

export const SYSTEM_TAG_UTILITIES =
  'bg-surface-default border-default text-default'
