import { Tag as TTag } from 'common/types/responses'
import type { ContentColour } from 'common/theme/tokens'

/** The design system's Content palette, one swatch per colour. */
export type TagSwatch = ContentColour

// Keyed on the colour already stored on the tag, so nothing needs migrating.
//
// The design system's Content palette is eleven colours where the picker
// offered twenty, so several of the old colours share a swatch. That loses
// less than it sounds: of the eleven pairs that now collide, nine were
// already indistinguishable, coral and maroon at dE 0.51. Only orange with
// amber and silver with slate gave up a real difference, both at dE ~10.9.
// Each colour maps to the Content hue nearest it.
const SWATCH_BY_COLOUR: Record<string, TagSwatch> = {
  '#039587': 'light-mint',
  '#1492f4': 'blue',
  '#14c0f4': 'light-blue',
  '#344562': 'blue',
  '#3cb371': 'light-green',
  '#3d4db6': 'blue',
  '#5b2c6f': 'light-purple',
  '#5d6d7e': 'light-grey',
  '#60bd4e': 'light-green',
  '#641e16': 'light-brown',
  '#aac200': 'light-yellow',
  '#c277e0': 'light-purple',
  '#c6b215': 'light-yellow',
  '#d35400': 'light-peach',
  '#d3d3d3': 'light-grey',
  '#de3163': 'light-pink',
  '#ea5a45': 'light-brown',
  '#f08080': 'light-red',
  '#fe5505': 'light-peach',
  '#ffa500': 'light-peach',
}

// The API takes any hex (`color` is a bare CharField with no validator), so a
// tag created outside the picker can hold a colour the scale does not cover.
const NEUTRAL_UTILITIES = 'bg-surface-subtle text-default'

export const getTagSwatch = (colour?: string | null): TagSwatch | null =>
  colour ? SWATCH_BY_COLOUR[colour.toLowerCase()] ?? null : null

export const getTagSwatchUtilities = (colour?: string | null): string => {
  const swatch = getTagSwatch(colour)
  return swatch ? `tag-${swatch}` : NEUTRAL_UTILITIES
}

export const isSystemTag = (tag: Partial<TTag>): boolean =>
  !!tag.type && tag.type !== 'NONE'

export const SYSTEM_TAG_UTILITIES =
  'bg-surface-default border-default text-default'
