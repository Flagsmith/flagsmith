import React, { FC } from 'react'
import { contentColours } from 'common/theme/tokens'
import Chip from 'components/base/Chip'
import { swatchLabel, swatchUtilities } from 'components/tags/tagSwatch'
import type { TagSwatch } from 'components/tags/tagSwatch'
import './TagColourPicker.scss'

type TagColourPickerProps = {
  value?: string
  onChange: (colour: string) => void
  className?: string
}

// The palette itself, so a picked colour is stored as it renders. Creating a
// tag from the search box already assigns from here.
const PALETTE = Object.entries(contentColours) as [TagSwatch, string][]

/** The swatch grid shared by the create/edit tag form and the inline picker. */
const TagColourPicker: FC<TagColourPickerProps> = ({
  className,
  onChange,
  value,
}) => (
  <div
    className={`tag-colour-picker d-flex flex-wrap gap-3 ${className ?? ''}`}
  >
    {PALETTE.map(([swatch, colour]) => (
      // A bare swatch, so it is named by its colour or it reaches a screen
      // reader as an unnamed button.
      <Chip
        key={colour}
        aria-label={swatchLabel(swatch)}
        className={swatchUtilities(swatch)}
        onClick={() => onChange(colour)}
        selected={value === colour}
        variant='none'
      />
    ))}
  </div>
)

export default TagColourPicker
