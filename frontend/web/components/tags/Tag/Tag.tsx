import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip from 'components/base/Chip'
import ColorSwatch from 'components/ColorSwatch'
import TagContent from 'components/tags/TagContent'
import Constants from 'common/constants'
import {
  getTagSwatch,
  getTagSwatchUtilities,
  swatchLabel,
  SYSTEM_TAG_UTILITIES,
  isSystemTag,
} from 'components/tags/utils'

type TagType = {
  className?: string
  // Whether the tag is unavailable to this organisation. The rule is a plan
  // entitlement, so it belongs to whoever knows about plans: see
  // Utils.tagDisabled. Reading it in here made a chip depend on AccountStore.
  disabled?: boolean
  // Partial, because `tag` is: the filter renders an "Untagged" pseudo-tag
  // with no id, and the create row previews a tag that does not exist yet.
  onClick?: (tag: Partial<TTag>) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

// Falls back to the raw value: a colour we never issued has no name but is
// still better than nothing in a screen reader.
const swatchName = (colour?: string | null) => {
  const swatch = getTagSwatch(colour)
  return swatch ? swatchLabel(swatch) : colour ?? undefined
}

export const getTagColor = (tag: Partial<TTag>) => {
  if (tag.type === 'UNHEALTHY') {
    return Constants.featureHealth.unhealthyColor
  }
  return tag.color
}

const Tag: FC<TagType> = ({
  className,
  disabled = false,
  isDot,
  onClick,
  selected,
  tag,
}) => {
  if (isDot) {
    // The stored colour, not the swatch: a tint this small would not read.
    return <ColorSwatch color={getTagColor(tag)} shape='circle' size='lg' />
  }

  // A system tag carries its state in the icon, so it keeps the plain surface.
  const isSystem = isSystemTag(tag)
  const colourUtilities = isSystem
    ? SYSTEM_TAG_UTILITIES
    : getTagSwatchUtilities(getTagColor(tag))

  return (
    <Chip
      // A tag with no text is a bare swatch, as in the colour picker, so it is
      // named by its colour or it reaches a screen reader as an unnamed button.
      aria-label={tag.label ? undefined : swatchName(getTagColor(tag))}
      className={cx(
        // Legacy `.chip` carried margin-right; the primitive does not, so tags
        // keep it here or they butt against whatever follows.
        'me-1',
        colourUtilities,
        { 'opacity-50': disabled },
        className,
      )}
      onClick={disabled || !onClick ? undefined : () => onClick(tag)}
      selected={selected}
      size='sm'
      variant='none'
    >
      <TagContent disabled={disabled} tag={tag} />
    </Chip>
  )
}

export default Tag
