import React, { FC, ReactNode } from 'react'
import cn from 'classnames'

interface FieldErrorProps {
  // The field-level error to show; renders nothing when falsy.
  error?: ReactNode
  className?: string
}

// Inline, per-field validation message shown beneath a control. This is the
// small-text counterpart to ErrorMessage (which is a banner alert for
// API/form-level errors) — use FieldError for a single field's validation.
const FieldError: FC<FieldErrorProps> = ({ className, error }) => {
  if (!error) {
    return null
  }
  return (
    <span className={cn('text-danger text-small', className)} role='alert'>
      {error}
    </span>
  )
}

export default FieldError
