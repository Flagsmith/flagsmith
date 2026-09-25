import React, { FC, useState } from 'react'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import Tag from './Tag'
import TagColourPicker from './TagColourPicker'

type ColourSelectType = {
  value: string
  onChange: (colour: string) => void
}

const ColourSelect: FC<ColourSelectType> = ({ onChange, value: _value }) => {
  const [isOpen, setIsOpen] = useState(false)
  const value = _value || Constants.tagColors[0]

  return (
    <>
      <Tag selected onClick={() => setIsOpen(true)} tag={{ color: value }} />

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
