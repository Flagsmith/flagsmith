import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import LabelWithTooltip from 'components/base/LabelWithTooltip'

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
// required indicator and an info-icon tooltip. The tooltip is rendered by the
// shared LabelWithTooltip (which uses the DS Tooltip), not hand-rolled here.
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
    <LabelWithTooltip
      label={
        <>
          {children}
          {required && (
            <span className='text-danger ml-1' aria-hidden>
              *
            </span>
          )}
        </>
      }
      tooltip={tooltip}
    />
  </label>
)

export default FieldLabel
