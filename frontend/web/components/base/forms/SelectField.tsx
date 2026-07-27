import React, { ReactNode, useId } from 'react'
import cn from 'classnames'
import { GroupBase, Props as ReactSelectProps } from 'react-select'
import { TooltipProps } from 'components/Tooltip'
import FieldError from './FieldError'
import FieldLabel from './FieldLabel'

// Props consumed by the field wrapper. Everything else is forwarded to Select.
interface OwnProps {
  title?: ReactNode
  // Base id for the field. The inner combobox input uses it (so the label's
  // htmlFor resolves) and the error derives `${id}-error` from it.
  id?: string
  error?: ReactNode
  required?: boolean
  tooltip?: string
  tooltipPlace?: TooltipProps['place']
  // Wrapper class; defaults to a form-group for consistent spacing.
  className?: string
  noMargin?: boolean
  'data-test'?: string
}

// Custom props our global Select adds on top of react-select.
interface BaseSelectExtras {
  size?: string
  autoSelect?: boolean
}

export type SelectFieldProps<
  Option = unknown,
  IsMulti extends boolean = false,
> = OwnProps &
  BaseSelectExtras &
  Omit<
    ReactSelectProps<Option, IsMulti, GroupBase<Option>>,
    | keyof OwnProps
    | keyof BaseSelectExtras
    | 'inputId'
    | 'aria-invalid'
    | 'aria-errormessage'
  >

// A labelled, accessible Select. The DS counterpart to InputGroup for a
// react-select control: it wires the label, the inline error, and the aria
// relationships off one id, so consumers stop wrapping a bare Select in
// InputGroup's `component` slot (which renders the control with no a11y
// wiring at all). Prefer this over `<InputGroup component={<Select />} />`.
//
// aria-errormessage (not aria-describedby) is deliberate: react-select v5
// forwards aria-errormessage/aria-invalid onto its combobox input on both
// render paths (searchable and not), but manages aria-describedby itself
// (placeholder/live-region), so describedby passed from outside never
// reaches the input.
function SelectField<Option = unknown, IsMulti extends boolean = false>({
  className,
  'data-test': dataTest,
  error,
  id,
  noMargin,
  required,
  title,
  tooltip,
  tooltipPlace,
  ...selectProps
}: SelectFieldProps<Option, IsMulti>) {
  const generatedId = useId()
  const inputId = id || generatedId
  const errorId = `${inputId}-error`
  const hasError = !!error

  return (
    <div
      className={cn(className, {
        'form-group': !noMargin,
        'select-field--invalid': hasError,
      })}
    >
      {(!!title || !!tooltip) && (
        <FieldLabel
          htmlFor={inputId}
          required={required}
          tooltip={tooltip}
          tooltipPlace={tooltipPlace}
        >
          {title}
        </FieldLabel>
      )}
      <Select
        {...selectProps}
        inputId={inputId}
        data-test={dataTest}
        aria-invalid={hasError || undefined}
        aria-errormessage={hasError ? errorId : undefined}
      />
      <FieldError id={errorId} error={error} />
    </div>
  )
}

export default SelectField
