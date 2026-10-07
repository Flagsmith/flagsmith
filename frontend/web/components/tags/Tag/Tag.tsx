import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import Chip, { ChipSize } from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import Constants from 'common/constants'
import TagContent from 'components/tags/TagContent'
import './Tag.scss'
import { swatchName, tagChipColour } from 'components/tags/utils'

type TagType = {
  className?: string
  // A plan entitlement, not a UI state. See Utils.tagDisabled.
  disabled?: boolean
  onClick?: (tag: Partial<TTag>) => void
  selected?: boolean
  // Small where a tag labels something, md where it is the thing chosen.
  size?: ChipSize
  // Partial: the archived and untagged pseudo-tags have no id.
  tag: Partial<TTag>
}

// Here rather than utils: Constants would drag the app tree into the swatch test.
export const getTagColor = (tag: Partial<TTag>) =>
  tag.type === 'UNHEALTHY' ? Constants.featureHealth.unhealthyColor : tag.color

const Tag: FC<TagType> = ({
  className,
  disabled = false,
  onClick,
  selected,
  size = 'sm',
  tag,
}) => {
  const isInteractive = !disabled && !!onClick
  const isToggle = isInteractive && selected !== undefined
  return (
    <Chip
      // A swatch has no text, and only a button can carry the name.
      aria-label={
        isInteractive && !tag.label ? swatchName(getTagColor(tag)) : undefined
      }
      aria-pressed={isToggle ? selected : undefined}
      {...tagChipColour(tag)}
      className={cx('me-1', { 'tag--swatch': !tag.label }, className)}
      onClick={isInteractive ? () => onClick?.(tag) : undefined}
      size={size}
    >
      {/* A swatch takes a box only once chosen, or the grid fills with empty
          outlines. */}
      {selected !== undefined && (tag.label || selected) && (
        <span
          className={cx(
            'tag-check d-inline-flex align-items-center justify-content-center flex-shrink-0 rounded-sm',
            { 'opacity-50': disabled, 'tag-check--on': selected },
          )}
        >
          {selected && (
            <Icon
              name='checkmark'
              width={14}
              fill='var(--ds-chip-fill, var(--color-surface-default))'
            />
          )}
        </span>
      )}
      <TagContent disabled={disabled} tag={tag} />
    </Chip>
  )
}

export default Tag
