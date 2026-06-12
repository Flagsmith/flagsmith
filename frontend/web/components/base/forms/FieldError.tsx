import React, { FC, ReactNode } from 'react'
import cn from 'classnames'

interface FieldErrorProps {
  // The field-level error to show; renders nothing when falsy.
  error?: ReactNode
  // Set so the control can reference it via aria-describedby.
  id?: string
  className?: string
}

// Inline, per-field validation message shown beneath a control. The small-text
// counterpart to ErrorMessage (which is a banner alert for API/form-level
// errors) — use FieldError for a single field's validation.
const FieldError: FC<FieldErrorProps> = ({ className, error, id }) => {
  if (!error) {
    return null
  }
  return (
    <span
      id={id}
      className={cn('text-danger text-small d-block mt-1', className)}
      role='alert'
    >
      {error}
    </span>
  )
}

export default FieldError
