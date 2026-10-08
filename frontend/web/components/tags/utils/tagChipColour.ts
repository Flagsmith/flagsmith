import { Tag as TTag } from 'common/types/responses'
import type { ChipColourChoice } from 'components/base/Chip/chipColour'
import { getTagSwatch } from './tagSwatch'
import { isSystemTag } from './systemTag'

// Every tag is a neutral chip. A system tag's state is in its icon, so it
// takes no dot; a custom tag's hue goes in one. A colour we never issued gets
// no dot rather than a guess at the nearest swatch.
export const tagChipColour = (tag: Partial<TTag>): ChipColourChoice => {
  if (isSystemTag(tag)) {
    return { variant: 'outline' }
  }
  return { dot: getTagSwatch(tag.color) ?? undefined, variant: 'neutral' }
}
