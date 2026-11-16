import { TAG_COLOURS } from 'common/theme/tagColours'
import { parseHex } from './parseHex'

type ColourSource = { banner_colour?: string | null }

// The banner colour is the only colour a user picks for an environment. Without
// a valid one, fall back to the colour the rest of the UI gives its list
// position. Always returns #RRGGBB: the API stores the banner colour unchecked.
export const getEnvironmentColour = (
  environment: ColourSource,
  index: number,
) => {
  const banner = environment.banner_colour?.trim()
  if (banner && parseHex(banner)) return `#${banner.replace(/^#/, '')}`
  return TAG_COLOURS[index % (TAG_COLOURS.length - 1)]
}

// The colour of the environment with this id. One missing from the list (for
// example without access) gets the first position's colour, never another
// environment's banner colour.
export const getEnvironmentColourById = (
  environments: (ColourSource & { id: number | string })[],
  id: number | string | undefined,
) => {
  const index = environments.findIndex((env) => `${env.id}` === `${id}`)
  return index === -1
    ? getEnvironmentColour({}, 0)
    : getEnvironmentColour(environments[index], index)
}
