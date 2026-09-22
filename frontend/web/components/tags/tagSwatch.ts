import { Tag as TTag } from 'common/types/responses'

export type TagSwatch =
  | 'indigo'
  | 'coral'
  | 'gold'
  | 'green'
  | 'orange'
  | 'blue'
  | 'cyan'
  | 'lavender'
  | 'teal'
  | 'navy'
  | 'amber'
  | 'mint'
  | 'silver'
  | 'slate'
  | 'maroon'
  | 'plum'
  | 'burnt-orange'
  | 'salmon'
  | 'lime'
  | 'cerise'

// Keyed on the colour already stored on the tag, so nothing needs migrating.
//
// One swatch per colour the picker offers, so no two tags render alike.
// Each is derived from that colour's own hue and validated at AA; the
// values are provisional until the palette work with design settles.
const SWATCH_BY_COLOUR: Record<string, TagSwatch> = {
  '#039587': 'teal',
  '#1492f4': 'blue',
  '#14c0f4': 'cyan',
  '#344562': 'navy',
  '#3cb371': 'mint',
  '#3d4db6': 'indigo',
  '#5b2c6f': 'plum',
  '#5d6d7e': 'slate',
  '#60bd4e': 'green',
  '#641e16': 'maroon',
  '#aac200': 'lime',
  '#c277e0': 'lavender',
  '#c6b215': 'gold',
  '#d35400': 'burnt-orange',
  '#d3d3d3': 'silver',
  '#de3163': 'cerise',
  '#ea5a45': 'coral',
  '#f08080': 'salmon',
  '#fe5505': 'orange',
  '#ffa500': 'amber',
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
