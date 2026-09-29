import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip from 'components/base/Chip'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import TagContent from './TagContent'
import Constants from 'common/constants'
import {
  SYSTEM_TAG_UTILITIES,
  getTagSwatch,
  getTagSwatchUtilities,
  isSystemTag,
} from './tagSwatch'

type TagType = {
  className?: string
  disabled?: boolean
  hideNames?: boolean
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

/** "light-green" reads as "Light green": a swatch has no other name. */
const swatchName = (colour?: string | null) => {
  const swatch = getTagSwatch(colour)
  if (!swatch) return colour ?? undefined
  const words = swatch.replace(/-/g, ' ')
  return words[0].toUpperCase() + words.slice(1)
}

export const getTagColor = (tag: Partial<TTag>) => {
  if (tag.type === 'UNHEALTHY') {
    return Constants.featureHealth.unhealthyColor
  }
  return tag.color
}

const Tag: FC<TagType> = ({
  className,
  disabled,
  hideNames,
  isDot,
  onClick,
  selected,
  tag,
}) => {
  if (isDot) {
    return (
      <div
        className={'tag--dot'}
        // No text on the dot, so the tag's own colour is safe here.
        style={{ backgroundColor: getTagColor(tag) }}
      />
    )
  }

  // A system tag carries its state in the icon, so it keeps the plain surface
  // whether it is being drawn or picked.
  const isSystem = isSystemTag(tag)
  const colourUtilities = isSystem
    ? SYSTEM_TAG_UTILITIES
    : getTagSwatchUtilities(getTagColor(tag))

  if (!hideNames && !!onClick) {
    return (
      <ToggleChip
        label={tag.label || swatchName(getTagColor(tag))}
        className={cx(colourUtilities, className)}
        active={selected}
        // No handler when disabled, so it is not a focusable button that does
        // nothing. The same rule as the drawn branch below.
        onClick={disabled ? undefined : () => onClick(tag as TTag)}
      >
        {!!tag.label && <TagContent disabled={disabled} tag={tag} />}
      </ToggleChip>
    )
  }

  // Hide unhealthy tags if feature is disabled
  if (
    !Utils.getFlagsmithHasFeature('feature_health') &&
    tag.type === 'UNHEALTHY'
  ) {
    return null
  }

  return (
    <Chip
      className={cx(
        // Legacy `.chip` carried margin-right; the primitive does not, so tags
        // keep it here or they butt against whatever follows.
        'me-1',
        colourUtilities,
        { 'opacity-50': disabled },
        className,
      )}
      onClick={disabled || !onClick ? undefined : () => onClick(tag as TTag)}
      size='xs'
      variant='none'
    >
      <TagContent disabled={disabled} tag={tag} />
    </Chip>
  )
}

export default Tag
