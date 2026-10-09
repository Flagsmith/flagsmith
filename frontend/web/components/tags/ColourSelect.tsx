import React, { FC, useState } from 'react'
import InlineModal from 'components/InlineModal'
import Constants from 'common/constants'
import BareButton from 'components/base/forms/BareButton'
import ColorSwatch from 'components/ColorSwatch'
import Icon from 'components/icons/Icon'
import { colorSurfaceDefault } from 'common/theme/tokens'

type ColourSelectType = {
  value: string
  onChange: (colour: string) => void
}

const ColourSelect: FC<ColourSelectType> = ({ onChange, value: _value }) => {
  const [isOpen, setIsOpen] = useState(false)
  const value = _value || Constants.tagColors[0]

  return (
    <>
      <BareButton aria-label='Select a colour' onClick={() => setIsOpen(true)}>
        <ColorSwatch color={value} size='xl' />
      </BareButton>

      <InlineModal
        title='Select a colour'
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        className='inline-modal--sm'
      >
        <Row className='mb-2 gap-4'>
          {Constants.tagColors.map((color: string) => (
            <BareButton
              aria-label={color}
              aria-pressed={value === color}
              className='position-relative d-inline-flex'
              key={color}
              onClick={() => {
                onChange(color)
                setIsOpen(false)
              }}
            >
              <ColorSwatch color={color} size='xl' />
              {value === color && (
                <Icon
                  className='position-absolute top-50 start-50 translate-middle'
                  fill={colorSurfaceDefault}
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
