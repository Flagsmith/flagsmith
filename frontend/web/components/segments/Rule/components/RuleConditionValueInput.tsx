import React from 'react'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'

import { getDarkMode } from 'project/darkMode'
import ModalHR from 'components/modals/ModalHR'
import EnvironmentSelectDropdown from './EnvironmentSelectDropdown'

type RuleConditionValueInputProps = {
  'data-test'?: string
  value: string | number | boolean
  style?: React.CSSProperties
  placeholder?: string
  onChange?: (value: string) => void
  disabled?: boolean
  readOnly?: boolean
  isValid?: boolean
  projectId?: number
  showEnvironmentDropdown?: boolean
  operator?: string
}

const TextAreaModal = ({
  disabled,
  isValid,
  onChange,
  placeholder,
  readOnly,
  style,
  value,
}: RuleConditionValueInputProps) => {
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

const RuleConditionValueInput: React.FC<RuleConditionValueInputProps> = ({
  isValid,
  onChange,
  operator,
  projectId,
  showEnvironmentDropdown,
  value,
  ...props
}) => {
  const checkWhitespaceIssues = () => {
    if (operator !== 'IN') return null
    if (typeof value !== 'string') return null

    const LEADING_WHITESPACE = /^\s/
    const TRAILING_WHITESPACE = /\s$/

    if (value.length >= 1 && value.trim() === '') {
      return { message: 'This value is only whitespaces' }
    }

    const items = value.split(',')
    
    if (items.length > 1) {
      const counts = items.reduce(
        (acc, item) => {
          const hasLeading = LEADING_WHITESPACE.test(item)
          const hasTrailing = TRAILING_WHITESPACE.test(item)
          
          if (hasLeading && hasTrailing) acc.both++
          else if (hasLeading) acc.leading++
          else if (hasTrailing) acc.trailing++
          
          return acc
        },
        { leading: 0, trailing: 0, both: 0 },
      )

      const totalIssues = counts.both + counts.leading + counts.trailing
      const hasMultipleIssues = [
        counts.both > 0,
        counts.leading > 0,
        counts.trailing > 0,
      ].filter(Boolean).length > 1

      if (totalIssues > 0) {
        if (hasMultipleIssues) {
          return {
            message: `${totalIssues} item(s) have whitespace issues`,
          }
        }
        
        if (counts.both > 0) {
          return {
            message: `${counts.both} item(s) have leading and trailing whitespaces`,
          }
        }
        if (counts.leading > 0) {
          return {
            message: `${counts.leading} item(s) have leading whitespaces`,
          }
        }
        if (counts.trailing > 0) {
          return {
            message: `${counts.trailing} item(s) have trailing whitespaces`,
          }
        }
      }
    }

    const hasLeading = LEADING_WHITESPACE.test(value)
    const hasTrailing = TRAILING_WHITESPACE.test(value)

    if (hasLeading && hasTrailing) {
      return {
        message: 'This value starts and ends with whitespaces',
      }
    }
    if (hasLeading) {
      return { message: 'This value starts with whitespaces' }
    }
    if (hasTrailing) {
      return { message: 'This value ends with whitespaces' }
    }

    return null
  }

  const whitespaceCheck = checkWhitespaceIssues()
  const hasWarning = !!whitespaceCheck
  const isLongText = String(value).length >= 10

  const validate = () => {
    if (whitespaceCheck?.message) {
      return whitespaceCheck.message
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
      {showEnvironmentDropdown && projectId ? (
        <EnvironmentSelectDropdown
          value={value}
          onChange={(value: string) => onChange?.(value)}
          projectId={projectId}
          dataTest={props['data-test']}
        />
      ) : (
        <>
          <Input
            type='text'
            data-test={props['data-test']}
            value={value}
            inputClassName={
              showIcon ? `pr-5 ${hasWarning ? 'border-warning' : ''}` : ''
            }
            style={{ width: '100%' }}
            onChange={(e: InputEvent) => {
              const value = Utils.safeParseEventValue(e)
              onChange?.(value)
            }}
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
                          onChange={onChange}
                          isValid={isValid}
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
        </>
      )}
    </div>
  )
}

export default RuleConditionValueInput
