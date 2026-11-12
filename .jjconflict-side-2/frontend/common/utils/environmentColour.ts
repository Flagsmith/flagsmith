import { TAG_COLOURS } from 'common/theme/tagColours'
import { toHexColour } from './hexColour'

type ColourSource = { banner_colour?: string | null }

// The banner colour, else the list position's colour. Normalised to #RRGGBB
// because the API doesn't validate the banner colour.
export const getEnvironmentColour = (
  environment: ColourSource,
  index: number,
) => {
  return (
    toHexColour(environment.banner_colour) ??
    TAG_COLOURS[index % TAG_COLOURS.length]
  )
}

// One missing from the list never borrows another environment's banner colour.
export const getEnvironmentColourById = (
  environments: (ColourSource & { id: number | string })[],
  id: number | string | undefined,
) => {
  const index = environments.findIndex((env) => `${env.id}` === `${id}`)
  return index === -1
    ? getEnvironmentColour({}, 0)
    : getEnvironmentColour(environments[index], index)
}
