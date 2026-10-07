import { Tag as TTag } from 'common/types/responses'
import type { ChipColourChoice } from 'components/base/Chip/chipColour'
import { getTagSwatch } from './tagSwatch'
import { isSystemTag } from './systemTag'

// A system tag's state is in its icon, so it takes no hue. A colour we never
// issued gets the neutral variant rather than a guess at the nearest swatch.
export const tagChipColour = (tag: Partial<TTag>): ChipColourChoice => {
  if (isSystemTag(tag)) {
    return { variant: 'outline' }
  }
  const swatch = getTagSwatch(tag.color)
  return swatch ? { colour: swatch } : { variant: 'neutral' }
}
