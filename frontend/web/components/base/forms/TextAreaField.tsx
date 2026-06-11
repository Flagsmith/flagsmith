import React, {
  FC,
  ReactNode,
  Ref,
  TextareaHTMLAttributes,
  useRef,
} from 'react'
import cn from 'classnames'
import Utils from 'common/utils/utils'
import Field from './Field'

interface TextAreaFieldProps
  extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: ReactNode
  // Field-level error; shows the message beneath the textarea when set.
  error?: ReactNode
  required?: boolean
  // Info-icon tooltip text shown next to the label.
  tooltip?: string
  // Styles the label/textarea/error wrapper; `textareaClassName` the textarea.
  wrapperClassName?: string
  textareaClassName?: string
  ref?: Ref<HTMLTextAreaElement>
}

// Field specialised to a textarea — the labelled, validated multi-line input.
const TextAreaField: FC<TextAreaFieldProps> = ({
  error,
  id,
  label,
  ref,
  required,
  textareaClassName,
  tooltip,
  wrapperClassName,
  ...rest
}) => {
  const generatedId = useRef(Utils.GUID()).current
  const fieldId = id ?? generatedId
  return (
    <Field
      label={label}
      error={error}
      required={required}
      tooltip={tooltip}
      htmlFor={fieldId}
      className={wrapperClassName}
    >
      <textarea
        {...rest}
        id={fieldId}
        ref={ref}
        className={cn(textareaClassName, { 'border-danger': !!error })}
      />
    </Field>
  )
}

export default TextAreaField
