import React, { FC, useState } from 'react'
import InlineModal from 'components/InlineModal'
import BareButton from 'components/base/forms/BareButton'
import ColorSwatch from 'components/ColorSwatch'
import { contentColours } from 'common/theme/tokens'
import TagColourPicker from 'components/tags/TagColourPicker'
import './ColourSelect.scss'

type ColourSelectType = {
  value: string
  onChange: (colour: string) => void
}

const ColourSelect: FC<ColourSelectType> = ({ onChange, value: _value }) => {
  const [isOpen, setIsOpen] = useState(false)
  const value = _value || contentColours.blue

  return (
    <>
      <BareButton
        aria-expanded={isOpen}
        aria-label='Select a colour'
        className='colour-select__trigger'
        onClick={() => setIsOpen(true)}
      >
        <ColorSwatch color={value} shape='rounded' size='xl' />
      </BareButton>

      <InlineModal
        title='Select a colour'
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        className='inline-modal--sm'
      >
        <TagColourPicker
          className='mb-2'
          onChange={(colour) => {
            onChange(colour)
            setIsOpen(false)
          }}
          value={value}
        />
      </InlineModal>
    </>
  )
}

export default ColourSelect
