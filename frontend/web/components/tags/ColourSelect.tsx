import React, { FC, useState } from 'react'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import Tag from './Tag'

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
        <div>
          <Row className='mb-2 gap-4'>
            {Constants.tagColors.map((color) => (
              <div key={color} className='tag--select'>
                <Tag
                  onClick={(tag) => {
                    onChange(tag.color)
                    setIsOpen(false)
                  }}
                  selected={value === color}
                  tag={{ color }}
                />
              </div>
            ))}
          </Row>
        </div>
      </InlineModal>
    </>
  )
}

export default ColourSelect
