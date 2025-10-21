import React, { FC } from 'react'
import cx from 'classnames'

import { Tag as TTag } from 'common/types/responses'
import ToggleChip from 'components/ToggleChip'
import Utils from 'common/utils/utils'
import TagContent from './TagContent'
import Constants from 'common/constants'
import { getDarkMode } from 'project/darkMode'
import Color from 'color'

type TagType = {
  className?: string
  hideNames?: boolean
  onClick?: (tag: TTag) => void
  selected?: boolean
  tag: Partial<TTag>
  isDot?: boolean
}

export const getTagColor = (tag: Partial<TTag>, selected?: boolean) => {
  if (getDarkMode() && tag.color === '#344562') {
    return '#9DA4AE'
  }
  if (tag.type === 'UNHEALTHY') {
    return Constants.featureHealth.unhealthyColor
  }
  if (selected) {
    return tag.color
  }
  return tag.color
}

export const TagWrapper = ({
  children,
  className,
  disabled,
  onClick,
  tag,
  tagColor,
}: any) => {
  return (
    <div
      onClick={() => {
        if (!disabled) {
          onClick?.(tag as TTag)
        }
      }}
      style={{
        backgroundColor: `${tagColor.fade(0.92)}`,
        border: `1px solid ${tagColor.fade(0.76)}`,
        color: `${tagColor.darken(0.1)}`,
      }}
      className={cx('chip', className)}
    >
      {children}
    </div>
  )
}

const Tag: FC<TagType> = ({
  className,
  hideNames,
  isDot,
  onClick,
  selected,
  tag,
}) => {
  const shouldLighten = (color: Color) => getDarkMode() && color.isDark();
  const tagColor = Utils.colour(getTagColor(tag, selected))
  if (isDot) {
    return (
      <div
        className={'tag--dot'}
        style={{
          backgroundColor: `${tagColor.darken(0.1)}`,
        }}
      />
    )
  }

  const disabled = Utils.tagDisabled(tag)

  if (!hideNames && !!onClick) {
    return (
      <ToggleChip
        color={shouldLighten(tagColor) ? tagColor.lighten(0.5) : tagColor}
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

  return (
    <TagWrapper
      tagColor={shouldLighten(tagColor) ? tagColor.lighten(0.5) : tagColor}
      className={className}
      disabled={disabled}
      hideNames={hideNames}
      isDot={isDot}
      onClick={onClick}
      selected={selected}
      tag={tag}
    >
      <TagContent tag={tag} />
    </TagWrapper>
  )
}

export default Tag
