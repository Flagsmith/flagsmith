import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import { TooltipProps } from 'components/Tooltip'
import FieldError from './FieldError'
import FieldLabel from './FieldLabel'

interface FieldProps {
  title?: ReactNode
  required?: boolean
  tooltip?: string
  tooltipPlace?: TooltipProps['place']
  // Wires the label to the control. Pass it when the child control accepts
  // an id; omitting it is a visible statement that the label is decorative.
  htmlFor?: string
  // Inline error rendered beneath the control. When htmlFor is set the error
  // gets `${htmlFor}-error`, so the control can reference it through
  // aria-describedby.
  error?: ReactNode
  className?: string
  noMargin?: boolean
  children: ReactNode
}

// The field skeleton: wrapper, label, control, error. Layout only — unlike
// the retired InputGroup `component` slot it never pretends to wire a
// control it cannot reach; wiring happens through the explicit htmlFor.
const Field: FC<FieldProps> = ({
  children,
  className,
  error,
  htmlFor,
  noMargin,
  required,
  title,
  tooltip,
  tooltipPlace,
}) => (
  <div className={cn(className, { 'form-group': !noMargin })}>
    {(!!title || !!tooltip) && (
      <FieldLabel
        htmlFor={htmlFor}
        required={required}
        tooltip={tooltip}
        tooltipPlace={tooltipPlace}
      >
        {title}
      </FieldLabel>
    )}
    {children}
    <FieldError id={htmlFor ? `${htmlFor}-error` : undefined} error={error} />
  </div>
)

export default Field
