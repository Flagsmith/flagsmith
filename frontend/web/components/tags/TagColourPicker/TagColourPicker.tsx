import React, { FC } from 'react'
import classNames from 'classnames'
import { contentColourNames, contentColours } from 'common/theme/tokens'
import BareButton from 'components/base/forms/BareButton'
import ColorSwatch from 'components/ColorSwatch'
import { swatchLabel, swatchUtilities } from 'components/tags/tagSwatch'
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
  <div
    className={`tag-colour-picker d-flex flex-wrap gap-3 ${className ?? ''}`}
  >
    {contentColourNames.map((swatch) => {
      const colour = contentColours[swatch]
      return (
        <BareButton
          key={swatch}
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
      )
    })}
  </div>
)

export default TagColourPicker
