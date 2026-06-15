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
import Icon from 'components/icons/Icon'
import { TooltipProps } from 'components/Tooltip'
import Input, { InputProps, InputSize } from './Input'

export interface InputGroupMethods {
  focus: () => void
}

interface InputGroupProps {
  className?: string
  noMargin?: boolean
  isInvalid?: boolean
  id?: string
  title?: ReactNode
  tooltip?: string
  tooltipPlace?: TooltipProps['place']
  hideTooltipIcon?: boolean
  unsaved?: boolean
  rightComponent?: ReactNode
  // Render an arbitrary control instead of the default Input/textarea.
  component?: ReactNode
  textarea?: boolean
  // Legacy: consumers pass truthy/falsy non-booleans (e.g. `name && name.length`);
  // coerced to a boolean before it reaches Input.
  isValid?: boolean | number | string | null
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
  /** @deprecated legacy top-level prop, never forwarded — set via inputProps */
  name?: string
  /** @deprecated legacy top-level prop, never forwarded — set via inputProps */
  autocomplete?: string
  /** @deprecated legacy top-level prop, never forwarded — set via inputProps */
  autoFocus?: boolean
  /** @deprecated legacy top-level prop, never forwarded — set via inputProps */
  autoValidate?: boolean
  /** @deprecated legacy top-level prop, never forwarded — set via inputProps */
  search?: boolean
  /** @deprecated legacy top-level prop, never forwarded — set via inputProps */
  rows?: number
  'data-test'?: string
  ref?: Ref<InputGroupMethods>
}

const InputGroup: FC<InputGroupProps> = ({
  className,
  component,
  'data-test': dataTest,
  defaultValue,
  disabled,
  hideTooltipIcon,
  id: idProp,
  inputProps,
  isInvalid,
  isValid,
  noMargin,
  onBlur,
  onChange,
  placeholder,
  ref,
  rightComponent,
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

  return (
    <div
      className={cn(className, {
        'form-group': !noMargin,
        'invalid': !!isInvalid,
      })}
    >
      {tooltip ? (
        <Tooltip
          title={
            <label
              htmlFor={id}
              className='cols-sm-2 control-label cursor-pointer'
            >
              <div>
                {title} {!hideTooltipIcon && <Icon name='info-outlined' />}{' '}
                {unsaved && <div className='unread'>Unsaved</div>}
              </div>
            </label>
          }
          place={tooltipPlace || 'top'}
        >
          {tooltip}
        </Tooltip>
      ) : (
        <Row>
          {!!title && (
            <Flex>
              <label htmlFor={id} className='cols-sm-2 control-label'>
                <div>
                  {title} {unsaved && <div className='unread'>Unsaved</div>}
                </div>
              </label>
            </Flex>
          )}
          {!!rightComponent && (
            <div style={{ marginBottom: '0.5rem' }}>{rightComponent}</div>
          )}
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
                onBlur={onBlur}
                placeholder={placeholder}
                size={size}
              />
            )}
          </div>
        )}
      </div>
      {error && (
        <span>
          <span
            id={inputProps?.name ? `${inputProps.name}-error` : ''}
            className='text-danger'
          >
            {typeof error === 'string'
              ? error
              : !!error?.length &&
                error.map((err, i) => <div key={i}>{err}</div>)}
          </span>
        </span>
      )}
    </div>
  )
}

InputGroup.displayName = 'InputGroup'

export default InputGroup
