import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon from 'components/icons/Icon'

interface FieldLabelProps {
  // Associates the label with its control; required for accessibility.
  htmlFor?: string
  children: ReactNode
  // Shows a danger asterisk after the label.
  required?: boolean
  // When set, an info icon follows the label and reveals this text on hover.
  tooltip?: string
  className?: string
}

// The label for a form field — wires `htmlFor` to the control, with an optional
// required indicator and an info-icon tooltip. Pair with FieldError + a control
// inside InputField, or use standalone.
const FieldLabel: FC<FieldLabelProps> = ({
  children,
  className,
  htmlFor,
  required,
  tooltip,
}) => (
  <label
    htmlFor={htmlFor}
    className={cn('control-label d-flex align-items-center', className)}
  >
    {children}
    {required && (
      <span className='text-danger ml-1' aria-hidden>
        *
      </span>
    )}
    {tooltip && (
      <span className='ml-1'>
        <Tooltip
          title={<Icon name='info-outlined' width={16} height={16} />}
          place='top'
          titleClassName='cursor-pointer'
        >
          {tooltip}
        </Tooltip>
      </span>
    )}
  </label>
)

export default FieldLabel
