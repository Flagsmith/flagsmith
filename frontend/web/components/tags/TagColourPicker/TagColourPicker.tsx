import React, { FC } from 'react'
import classNames from 'classnames'
import { contentColourNames, contentColours } from 'common/theme/tokens'
import BareButton from 'components/base/forms/BareButton'
import ColorSwatch from 'components/ColorSwatch'
import {
  getTagSwatch,
  swatchLabel,
  swatchUtilities,
} from 'components/tags/utils'
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
}) => {
  // By swatch, not by hex: a tag made before this palette holds a colour that
  // is none of these, and it still renders as one of them.
  const selected = getTagSwatch(value)

  return (
    <div className={classNames('d-flex flex-wrap gap-3', className)}>
      {contentColourNames.map((swatch) => (
        <BareButton
          key={swatch}
          aria-label={swatchLabel(swatch)}
          aria-pressed={selected === swatch}
          className={classNames('tag-colour-picker__swatch', {
            'tag-colour-picker__swatch--selected': selected === swatch,
          })}
          onClick={() => onChange(contentColours[swatch])}
        >
          <ColorSwatch
            className={swatchUtilities(swatch)}
            shape='rounded'
            size='2xl'
          />
        </BareButton>
      ))}
    </div>
  )
}

export default TagColourPicker
