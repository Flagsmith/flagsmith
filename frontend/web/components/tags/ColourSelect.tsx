import React, { FC, useState } from 'react'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import BareButton from 'components/base/forms/BareButton'
import ColorSwatch from 'components/ColorSwatch'
import Icon from 'components/icons/Icon'
import { contentColours, contentInk } from 'common/theme/tokens'
import { contrastRatio } from 'common/theme/contrast'

type ColourSelectType = {
  value: string
  onChange: (colour: string) => void
}

// The tick sits on the colour itself, which is a hex a user picked rather than
// a token, so neither ink nor pale reads on all of them. Pick per colour.
const tickFill = (colour: string) =>
  contrastRatio(contentInk, colour) >
  contrastRatio(contentColours['light-grey'], colour)
    ? contentInk
    : contentColours['light-grey']

// The banner colour, not a tag: these are raw hexes rather than the tag
// palette, so they render as themselves rather than through a swatch lookup.
const ColourSelect: FC<ColourSelectType> = ({ onChange, value: _value }) => {
  const [isOpen, setIsOpen] = useState(false)
  const value = _value || Constants.tagColors[0]

  return (
    <>
      <BareButton onClick={() => setIsOpen(true)}>
        <ColorSwatch color={value} size='xl' />
      </BareButton>

      <InlineModal
        title='Select a colour'
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        className='inline-modal--sm'
      >
        <Row className='mb-2 gap-4'>
          {Constants.tagColors.map((colour) => (
            <BareButton
              aria-pressed={value === colour}
              className='position-relative d-inline-flex'
              key={colour}
              onClick={() => {
                onChange(colour)
                setIsOpen(false)
              }}
            >
              <ColorSwatch color={colour} size='xl' />
              {value === colour && (
                <Icon
                  className='position-absolute top-50 start-50 translate-middle'
                  fill={tickFill(colour)}
                  name='checkmark'
                  width={14}
                />
              )}
            </BareButton>
          ))}
        </Row>
      </InlineModal>
    </>
  )
}

export default ColourSelect
