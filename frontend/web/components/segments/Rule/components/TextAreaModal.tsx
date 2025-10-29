import React, { useState, FC } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import ModalHR from 'components/modals/ModalHR'
import { checkWhitespaceIssues } from 'components/segments/Rule/utils'

type TextAreaModalProps = {
  value: string | number | boolean
  onChange?: (value: string) => void
  operator?: string
}

const TextAreaModal: FC<TextAreaModalProps> = ({
  onChange,
  operator,
  value,
}) => {
  const [textAreaValue, setTextAreaValue] = useState(value)
  const whitespaceCheck = checkWhitespaceIssues(textAreaValue, operator)
  const hasWarning = !!whitespaceCheck

  return (
    <div>
      <div className='modal-body d-flex flex-column gap-1'>
        <InputGroup
          id='rule-value-textarea'
          data-test='rule-value-textarea'
          value={textAreaValue}
          onChange={(e: InputEvent) => {
            const value = Utils.safeParseEventValue(e)
            setTextAreaValue(value.replace(/\n/g, ''))
          }}
          noMargin
          inputProps={{
            className: hasWarning ? 'border-warning' : '',
          }}
          type='text'
          className='w-100'
          textarea
        />
        <div
          style={{
            minHeight: '20px',
            opacity: hasWarning ? 1 : 0,
            transition: 'opacity 0.25s ease-in-out',
          }}
        >
          {hasWarning && (
            <div className='text-warning d-flex align-items-start gap-2'>
              <span className='d-flex' style={{ alignSelf: 'center' }}>
                <Icon name='warning' width={16} height={16} />
              </span>
              <span>{whitespaceCheck?.message}</span>
            </div>
          )}
        </div>
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
