import React, { FC } from 'react'
import Constants from 'common/constants'
import Tag from 'components/tags/Tag'
import './TagColourPicker.scss'

type TagColourPickerProps = {
  value?: string
  onChange: (colour: string) => void
  className?: string
}

/** The swatch grid shared by the create/edit tag form and the inline picker. */
const TagColourPicker: FC<TagColourPickerProps> = ({
  className,
  onChange,
  value,
}) => (
  <div className={`tag-colour-picker ${className ?? ''}`}>
    {Constants.tagColors.map((colour: string) => (
      <Tag
        key={colour}
        onClick={(tag) => onChange(tag.color)}
        selected={value === colour}
        tag={{ color: colour }}
      />
    ))}
  </div>
)

export default TagColourPicker
