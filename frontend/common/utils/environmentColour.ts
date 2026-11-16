import { TAG_COLOURS } from 'common/theme/tagColours'
import { parseHex } from './parseHex'

// The banner colour is the only colour a user picks for an environment. Without
// one, fall back to the colour the rest of the UI gives its list position.
export const getEnvironmentColour = (
  environment: { banner_colour?: string | null },
  index: number,
) =>
  environment.banner_colour && parseHex(environment.banner_colour)
    ? environment.banner_colour
    : TAG_COLOURS[index % (TAG_COLOURS.length - 1)]
