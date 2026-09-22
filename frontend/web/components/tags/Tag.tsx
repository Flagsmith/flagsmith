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
  getTagSwatchUtilities,
  isSystemTag,
} from './tagSwatch'

type TagType = {
  className?: string
  hideNames?: boolean
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

export const getTagColor = (tag: Partial<TTag>) => {
  if (tag.type === 'UNHEALTHY') {
    return Constants.featureHealth.unhealthyColor
  }
  return tag.color
}

const Tag: FC<TagType> = ({
  className,
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

  const disabled = Utils.tagDisabled(tag)

  if (!hideNames && !!onClick) {
    return (
      <ToggleChip
        className={cx(getTagSwatchUtilities(getTagColor(tag)), className)}
        active={selected}
        onClick={() => {
          if (!disabled) {
            onClick?.(tag as TTag)
          }
        }}
      >
        {!!tag.label && <TagContent tag={tag} />}
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

  const isSystem = isSystemTag(tag)

  return (
    <Chip
      className={cx(
        // Legacy `.chip` carried margin-right; the primitive does not, so tags
        // keep it here or they butt against whatever follows.
        'me-1',
        isSystem
          ? SYSTEM_TAG_UTILITIES
          : getTagSwatchUtilities(getTagColor(tag)),
        // The fill carries the colour, so a border would double the edge.
        { 'border-0': !isSystem, 'opacity-50': disabled },
        className,
      )}
      onClick={disabled || !onClick ? undefined : () => onClick(tag as TTag)}
      size='xs'
      variant='none'
    >
      <TagContent tag={tag} />
    </Chip>
  )
}

export default Tag
