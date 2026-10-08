import { contentColourNames, contentColours } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'

type TagSwatch = ContentColour

// Existing tags to the palette that replaced them (#8465): Constants.tagColors
// plus the archived and untagged pseudo-tags, and the pale fills this scale
// replaced, which only ever reached a preview deploy.
const LEGACY_COLOURS: Record<string, TagSwatch> = {
  '#039587': 'mint',
  '#1492f4': 'blue',
  '#14c0f4': 'sky',
  // Navy and slate carry a hue but never showed one: both were drawn as an 8%
  // wash, so what a user has always seen is grey.
  '#344562': 'grey',
  '#3cb371': 'green',
  '#3d4db6': 'blue',
  '#5b2c6f': 'purple',
  '#5d6d7e': 'grey',
  '#60bd4e': 'green',
  '#641e16': 'brown',
  '#8f8f8f': 'grey',
  '#aac200': 'yellow',
  '#c277e0': 'purple',
  '#c6b215': 'yellow',
  '#c7e6ff': 'blue',
  '#c7e7e2': 'mint',
  '#c9f1fe': 'sky',
  '#d35400': 'peach',
  '#d3d3d3': 'grey',
  '#d6f1d4': 'green',
  '#dacdde': 'purple',
  '#de3163': 'pink',
  '#dedede': 'grey',
  '#dfc8c6': 'brown',
  // Coral is a red, not a brown. brown is 3deg closer in hue but 72
  // points less saturated, so it reads as neither.
  '#ea5a45': 'red',
  '#eff0f3': 'grey',
  '#f08080': 'red',
  '#f3edca': 'yellow',
  '#fcd6c7': 'peach',
  '#fe5505': 'peach',
  '#ffa500': 'peach',
  '#ffceda': 'pink',
  '#ffe0df': 'red',
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
