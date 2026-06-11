import React, { FC, ReactNode, Ref, useRef } from 'react'
import cn from 'classnames'
import Input, { InputMethods, InputProps } from './Input'
import Utils from 'common/utils/utils'
import FieldLabel from './FieldLabel'
import FieldError from './FieldError'

interface InputFieldProps extends Omit<InputProps, 'isValid'> {
  // Field label; wired to the input via htmlFor/id.
  label?: ReactNode
  // Field-level error. When set, the input shows its invalid state and the
  // message renders beneath it. Controlled — the consumer decides when an error
  // is present, so this works with manual state or any form library.
  error?: ReactNode
  required?: boolean
  // Info-icon tooltip text shown next to the label.
  tooltip?: string
  // Styles the label/input/error wrapper; `inputClassName` styles the input.
  wrapperClassName?: string
  ref?: Ref<InputMethods>
}

// Composes FieldLabel + Input + FieldError into one labelled, validated field —
// the typed successor to InputGroup. Presentational and library-agnostic: pass
// `error` and it surfaces both the invalid styling and the message.
const InputField: FC<InputFieldProps> = ({
  error,
  id,
  label,
  ref,
  required,
  tooltip,
  wrapperClassName,
  ...inputProps
}) => {
  const generatedId = useRef(Utils.GUID()).current
  const fieldId = id ?? generatedId
  return (
    <div className={cn('form-group', wrapperClassName)}>
      {label && (
        <FieldLabel htmlFor={fieldId} required={required} tooltip={tooltip}>
          {label}
        </FieldLabel>
      )}
      <Input
        {...inputProps}
        id={fieldId}
        ref={ref}
        // Derive the input's invalid state from `error`. autoValidate shows it
        // immediately (rather than after blur) to match the message; this maps
        // to a controlled `invalid` prop once Input is slimmed.
        isValid={!error}
        autoValidate={!!error}
      />
      <FieldError error={error} />
    </div>
  )
}

export default InputField
