import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'

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
// required indicator and an info-icon tooltip (rendered with the DS Tooltip).
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
      <Tooltip
        title={<Icon name='info-outlined' width={12} height={12} />}
        place='top'
        titleClassName='cursor-pointer ml-1'
      >
        {tooltip}
      </Tooltip>
    )}
  </label>
)

export default FieldLabel
