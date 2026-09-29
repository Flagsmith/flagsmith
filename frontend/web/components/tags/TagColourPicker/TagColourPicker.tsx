import React, { FC } from 'react'
import classNames from 'classnames'
import { contentColours } from 'common/theme/tokens'
import BareButton from 'components/base/forms/BareButton'
import ColorSwatch from 'components/ColorSwatch'
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
      // The swatch is decorative, so the button carries the name and the state.
      <BareButton
        key={colour}
        aria-label={swatchLabel(swatch)}
        aria-pressed={value === colour}
        className={classNames('tag-colour-picker__swatch', {
          'tag-colour-picker__swatch--selected': value === colour,
        })}
        onClick={() => onChange(colour)}
      >
        <ColorSwatch
          className={swatchUtilities(swatch)}
          shape='rounded'
          size='xl'
        />
      </BareButton>
    ))}
  </div>
)

export default TagColourPicker
