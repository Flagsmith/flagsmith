import React, {
  FC,
  FocusEventHandler,
  ReactNode,
  Ref,
  useId,
  useImperativeHandle,
  useRef,
} from 'react'
import cn from 'classnames'
import { TooltipProps } from 'components/Tooltip'
import Flex from 'components/base/grid/Flex'
import Row from 'components/base/grid/Row'
import FieldError from './FieldError'
import FieldLabel from './FieldLabel'
import Input, { InputProps, InputSize } from './Input'

export interface InputGroupMethods {
  focus: () => void
}

type InputGroupValidity = boolean | number | string | null

interface InputGroupProps {
  className?: string
  noMargin?: boolean
  isInvalid?: boolean
  id?: string
  title?: ReactNode
  tooltip?: string
  tooltipPlace?: TooltipProps['place']
  unsaved?: boolean
  // Render an arbitrary control instead of the default Input/textarea.
  component?: ReactNode
  textarea?: boolean
  // Legacy: consumers pass truthy/falsy non-booleans (e.g. `name && name.length`);
  // coerced to a boolean before it reaches Input.
  isValid?: InputGroupValidity
  disabled?: boolean
  value?: InputProps['value']
  defaultValue?: InputProps['defaultValue']
  // Legacy escape hatch: consumers annotate the event variously (Event,
  // InputEvent, ChangeEvent), so this stays permissive.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onChange?: (event: any) => void
  onBlur?: FocusEventHandler<HTMLInputElement | HTMLTextAreaElement>
  type?: string
  placeholder?: string
  size?: InputSize
  // Spread onto the underlying control; `error` is consumed here (not spread).
  // Loosely typed to tolerate the legacy grab-bag of props consumers pass.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  inputProps?: Record<string, any> & {
    error?: string | string[]
    name?: string
  }
  'data-test'?: string
  ref?: Ref<InputGroupMethods>
}

const InputGroup: FC<InputGroupProps> = ({
  className,
  component,
  'data-test': dataTest,
  defaultValue,
  disabled,
  id: idProp,
  inputProps,
  isInvalid,
  isValid,
  noMargin,
  onBlur,
  onChange,
  placeholder,
  ref,
  size,
  textarea,
  title,
  tooltip,
  tooltipPlace,
  type,
  unsaved,
  value,
}) => {
  const generatedId = useId()
  const id = idProp || generatedId
  const inputRef = useRef<{ focus: () => void } | null>(null)
  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
  }))

  const { error, ...restInputProps } = inputProps ?? {}
  // Wire label -> control -> error off the same id so screen readers announce
  // the message for this field (htmlFor/id/aria-describedby all share `id`).
  const errorId = `${id}-error`
  const hasError = Array.isArray(error) ? error.length > 0 : !!error
  let errorContent: ReactNode = null
  if (typeof error === 'string') {
    errorContent = error
  } else if (Array.isArray(error) && error.length) {
    errorContent = error.map((err, i) => <div key={i}>{err}</div>)
  }

  return (
    <div
      className={cn(className, {
        'form-group': !noMargin,
        'invalid': !!isInvalid,
      })}
    >
      {(!!title || !!tooltip) && (
        <Row>
          <Flex>
            <FieldLabel
              htmlFor={id}
              className='cols-sm-2'
              tooltip={tooltip}
              tooltipPlace={tooltipPlace}
            >
              {title}
              {unsaved && <div className='unread ml-1'>Unsaved</div>}
            </FieldLabel>
          </Flex>
        </Row>
      )}

      <div>
        {component ? (
          component
        ) : (
          <div>
            {textarea ? (
              <textarea
                ref={(c) => {
                  inputRef.current = c
                }}
                {...(restInputProps as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
                disabled={disabled}
                value={value}
                defaultValue={defaultValue}
                data-test={dataTest}
                onChange={onChange}
                id={id}
                aria-invalid={hasError}
                aria-describedby={hasError ? errorId : undefined}
                placeholder={placeholder}
                onBlur={onBlur}
              />
            ) : (
              <Input
                ref={(c) => {
                  inputRef.current = c
                }}
                {...restInputProps}
                isValid={
                  isValid === null || isValid === undefined
                    ? undefined
                    : !!isValid
                }
                disabled={disabled}
                defaultValue={defaultValue}
                value={value}
                data-test={dataTest}
                onChange={onChange}
                type={type || 'text'}
                id={id}
                aria-invalid={hasError}
                aria-describedby={hasError ? errorId : undefined}
                onBlur={onBlur}
                placeholder={placeholder}
                size={size}
              />
            )}
          </div>
        )}
      </div>
      <FieldError id={errorId} error={errorContent} />
    </div>
  )
}

InputGroup.displayName = 'InputGroup'

export default InputGroup
