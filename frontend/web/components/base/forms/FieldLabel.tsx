import React, { FC, ReactNode } from 'react'
import cn from 'classnames'

interface FieldLabelProps {
  // Associates the label with its control; required for accessibility.
  htmlFor?: string
  children: ReactNode
  // Shows a danger asterisk after the label.
  required?: boolean
  className?: string
}

// The label for a form field — wires `htmlFor` to the control and renders an
// optional required indicator. Pair with FieldError + a control inside
// InputField, or use standalone.
const FieldLabel: FC<FieldLabelProps> = ({
  children,
  className,
  htmlFor,
  required,
}) => (
  <label htmlFor={htmlFor} className={cn('control-label', className)}>
    {children}
    {required && (
      <span className='text-danger ml-1' aria-hidden>
        *
      </span>
    )}
  </label>
)

export default FieldLabel
