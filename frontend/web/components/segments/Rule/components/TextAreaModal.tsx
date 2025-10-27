import React, { useState, FC } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import ModalHR from 'components/modals/ModalHR'

type TextAreaModalProps = {
  value: string | number | boolean
  onChange?: (value: string) => void
}

const TextAreaModal: FC<TextAreaModalProps> = ({ onChange, value }) => {
  const [textAreaValue, setTextAreaValue] = useState(value)

  return (
    <div>
      <div className='modal-body'>
        <InputGroup
          id='rule-value-textarea'
          data-test='rule-value-textarea'
          value={textAreaValue}
          onChange={(e: InputEvent) => {
            const value = Utils.safeParseEventValue(e)
            setTextAreaValue(value.replace(/\n/g, ''))
          }}
          type='text'
          className='w-100'
          textarea
        />
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button
          className='mr-2'
          theme='secondary'
          id='rule-value-textarea-cancel'
          data-tests='rule-value-textarea-cancel'
          onClick={closeModal2}
        >
          Cancel
        </Button>
        <Button
          type='button'
          id='rule-value-textarea-save'
          data-tests='rule-value-textarea-save'
          onClick={() => {
            const event = new InputEvent('input', { bubbles: true })
            Object.defineProperty(event, 'target', {
              value: { value: textAreaValue },
              writable: false,
            })
            const value = Utils.getTypedValue(Utils.safeParseEventValue(event))
            onChange?.(value)
            closeModal2()
          }}
        >
          Apply
        </Button>
      </div>
    </div>
  )
}

export default TextAreaModal
