import React from 'react'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'

import { getDarkMode } from 'project/darkMode'
import ModalHR from 'components/modals/ModalHR'

type RuleConditionInputValueProps = {
  'data-test'?: string
  value: string | number
  style?: React.CSSProperties
  placeholder?: string
  onChange?: (e: InputEvent) => void
  disabled?: boolean
  readOnly?: boolean
  isValid?: boolean
}

const TextAreaModal = ({
  disabled,
  isValid,
  onChange,
  placeholder,
  readOnly,
  style,
  value,
}: RuleConditionInputValueProps) => {
  const [textAreaValue, setTextAreaValue] = React.useState(value)

  return (
    <div>
      <div className='modal-body'>
        <InputGroup
          id='rule-value-textarea'
          data-test='rule-value-textarea'
          value={textAreaValue}
          inputProps={{
            style: style,
          }}
          isValid={isValid}
          onChange={(e: InputEvent) => {
            const value = Utils.safeParseEventValue(e)
            setTextAreaValue(value.replace(/\n/g, ''))
          }}
          type='text'
          className='w-100'
          readOnly={readOnly}
          placeholder={placeholder}
          disabled={disabled}
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
            onChange?.(event)
            closeModal2()
          }}
        >
          Apply
        </Button>
      </div>
    </div>
  )
}

const RuleConditionInputValue = (props: RuleConditionInputValueProps) => {
  const value = props.value
  const hasLeadingWhitespace = typeof value === 'string' && /^\s/.test(value)
  const hasTrailingWhitespace = typeof value === 'string' && /\s$/.test(value)
  const isOnlyWhitespace =
    typeof value === 'string' && value.length >= 1 && value.trim() === ''

  const hasBothLeadingAndTrailingWhitespace =
    hasLeadingWhitespace && hasTrailingWhitespace
  const hasWarning =
    hasLeadingWhitespace ||
    hasTrailingWhitespace ||
    hasBothLeadingAndTrailingWhitespace ||
    isOnlyWhitespace
  const isLongText = String(value).length >= 10

  const validate = () => {
    if (isOnlyWhitespace) {
      return 'This value is only whitespaces'
    }
    if (hasBothLeadingAndTrailingWhitespace) {
      return 'This value starts and ends with whitespaces'
    }
    if (hasLeadingWhitespace) {
      return 'This value starts with whitespaces'
    }
    if (hasTrailingWhitespace) {
      return 'This value ends with whitespaces'
    }
    if (isLongText) {
      return 'Click to edit text in a larger area'
    }
    return ''
  }

  const showIcon = hasWarning || isLongText
  const isDarkMode = getDarkMode()

  return (
    <div className='relative'>
      <Input
        type='text'
        {...props}
        inputClassName={
          showIcon ? `pr-5 ${hasWarning ? 'border-warning' : ''}` : ''
        }
      />
      {showIcon && (
        <div style={{ position: 'absolute', right: 5, top: 9 }}>
          <Tooltip
            title={
              <div
                className={`flex ${
                  isDarkMode ? 'bg-white' : 'bg-black'
                } bg-opacity-10 rounded-2 p-1 ${
                  hasWarning ? '' : 'cursor-pointer'
                }`}
                onClick={() => {
                  if (hasWarning) return
                  openModal2(
                    'Edit Value',
                    <TextAreaModal
                      value={value}
                      onChange={props.onChange}
                      isValid={props.isValid}
                    />,
                  )
                }}
              >
                <Icon
                  name={hasWarning ? 'warning' : 'expand'}
                  fill={
                    hasWarning
                      ? undefined
                      : `${isDarkMode ? '#fff' : '#1A2634'}`
                  }
                  width={18}
                  height={18}
                />
              </div>
            }
            place='top'
            effect='solid'
          >
            {validate()}
          </Tooltip>
        </div>
      )}
    </div>
  )
}

export default RuleConditionInputValue
