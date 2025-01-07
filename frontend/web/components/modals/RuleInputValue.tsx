import React, { RefObject, useRef } from 'react'
import Input from 'components/base/forms/Input'

type RuleInputValueProps = {
  'data-test'?: string
  value: string | number
  style?: React.CSSProperties
  placeholder?: string
  onChange?: (e: InputEvent) => void
  disabled?: boolean
  readOnly?: boolean
  isValid?: boolean
  error?: string
}

const RuleInputValue = (props: RuleInputValueProps) => {
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
  const isLargeText = String(value).length >= 8

  const ref = useRef(null)

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
    if (isLargeText) {
      return String(value)
    }
    return ''
  }

  return (
    <Tooltip
      title={
        <div>
          <Input
            type='text'
            {...props}
            ref={ref}
            inputClassName={hasWarning && 'border-warning'}
          />
        </div>
      }
      place='top'
      effect='solid'
      afterShow={() => {
        ;(ref as RefObject<HTMLElement>).current?.focus()
      }}
    >
      {validate()}
    </Tooltip>
  )
}

export default RuleInputValue
