import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import FieldLabel from './FieldLabel'
import FieldError from './FieldError'

interface FieldProps {
  // The control this field wraps — an Input, Select, textarea, or anything.
  children: ReactNode
  label?: ReactNode
  // Field-level error; shows the message beneath the control when set.
  error?: ReactNode
  required?: boolean
  // Info-icon tooltip text shown next to the label.
  tooltip?: string
  // Should match the control's id so the label points at it.
  htmlFor?: string
  className?: string
}

// The generic form-field wrapper: FieldLabel (+ tooltip/required) + a control +
// FieldError. Library-agnostic and control-agnostic — InputField, SelectField
// and TextAreaField are thin specialisations, and any custom control can be
// dropped in directly (the typed replacement for InputGroup's `component=`).
const Field: FC<FieldProps> = ({
  children,
  className,
  error,
  htmlFor,
  label,
  required,
  tooltip,
}) => (
  <div className={cn('form-group', className)}>
    {label && (
      <FieldLabel htmlFor={htmlFor} required={required} tooltip={tooltip}>
        {label}
      </FieldLabel>
    )}
    {children}
    <FieldError error={error} />
  </div>
)

export default Field
