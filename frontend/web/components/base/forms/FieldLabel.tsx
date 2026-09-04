import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon from 'components/icons/Icon'
import Tooltip, { TooltipProps } from 'components/Tooltip'

interface FieldLabelProps {
  htmlFor?: string
  id?: string
  children: ReactNode
  // Shows a danger asterisk after the label.
  required?: boolean
  // When set, an info icon follows the label and reveals this text on hover.
  tooltip?: string
  // Placement of the tooltip relative to the icon (defaults to 'top').
  tooltipPlace?: TooltipProps['place']
  className?: string
}

// The label for a form field — wires `htmlFor` to the control, with an optional
// required indicator and an info-icon tooltip (rendered with the DS Tooltip).
const FieldLabel: FC<FieldLabelProps> = ({
  children,
  className,
  htmlFor,
  id,
  required,
  tooltip,
  tooltipPlace = 'top',
}) => (
  <label
    id={id}
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
        title={<Icon name='info-outlined' width={16} height={16} />}
        place={tooltipPlace}
        titleClassName='cursor-pointer ml-1 d-inline-flex align-items-center'
      >
        {tooltip}
      </Tooltip>
    )}
  </label>
)

export default FieldLabel
