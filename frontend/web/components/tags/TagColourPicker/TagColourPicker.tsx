import React, { FC } from 'react'
import { contentColours } from 'common/theme/tokens'
import Tag from 'components/tags/Tag'
import './TagColourPicker.scss'

type TagColourPickerProps = {
  value?: string
  onChange: (colour: string) => void
  className?: string
}

// The palette itself, so a picked colour is stored as it renders. Creating a
// tag from the search box already assigns from here.
const PALETTE = Object.values(contentColours)

/** The swatch grid shared by the create/edit tag form and the inline picker. */
const TagColourPicker: FC<TagColourPickerProps> = ({
  className,
  onChange,
  value,
}) => (
  <div
    className={`tag-colour-picker d-flex flex-wrap gap-3 ${className ?? ''}`}
  >
    {PALETTE.map((colour) => (
      <Tag
        key={colour}
        onClick={() => onChange(colour)}
        selected={value === colour}
        tag={{ color: colour }}
      />
    ))}
  </div>
)

export default TagColourPicker
