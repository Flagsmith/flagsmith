import React, {
  FocusEvent,
  KeyboardEvent,
  Ref,
  useImperativeHandle,
  useRef,
  useState,
} from 'react'
import cn from 'classnames'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'
import { colorIconDanger } from 'common/theme/tokens'

export type InputSize = 'default' | 'large' | 'small' | 'xSmall'

// Imperative API exposed via ref (React 19 ref-as-prop, no forwardRef).
// focus() is a no-op under E2E, matching the original behaviour.
export interface InputMethods {
  focus: () => void
}

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  autoValidate?: boolean
  // Custom lowercase alias for the standard `autoComplete`, kept for back-compat.
  autocomplete?: string
  centered?: boolean
  enableAutoComplete?: string
  inputClassName?: string
  isValid?: boolean
  ref?: Ref<InputMethods>
  search?: boolean
  showSuccess?: boolean
  size?: InputSize
  underline?: boolean
}

const sizeClassNames: Record<InputSize, string> = {
  default: '',
  large: 'input-lg',
  small: 'input-sm',
  xSmall: 'input-xsm',
}

// Width of the password reveal / search icons per input size.
const iconWidthBySize: Record<InputSize, number | undefined> = {
  default: undefined,
  large: 24,
  small: 20,
  xSmall: 18,
}

const Input: React.FC<InputProps> = ({
  autoValidate,
  autocomplete,
  centered,
  className = '',
  disabled,
  enableAutoComplete,
  inputClassName,
  isValid = true,
  onBlur: onBlurProp,
  onChange,
  onFocus: onFocusProp,
  onKeyDown: onKeyDownProp,
  ref,
  search,
  showSuccess,
  size,
  type: typeProp,
  underline,
  value,
  ...rest
}) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isFocused, setIsFocused] = useState(false)
  const [shouldValidate, setShouldValidate] = useState(
    !!value || !!autoValidate,
  )
  const [type, setType] = useState(typeProp)

  // No-op under E2E to avoid programmatic focus stealing during tests; native
  // autoFocus is unaffected. Matches the original Input.focus() behaviour.
  useImperativeHandle(ref, () => ({
    focus: () => {
      if (E2E) return
      inputRef.current?.focus()
    },
  }))

  const onFocus = (e: FocusEvent<HTMLInputElement>) => {
    setIsFocused(true)
    onFocusProp?.(e)
  }

  const onBlur = (e: FocusEvent<HTMLInputElement>) => {
    setIsFocused(false)
    setShouldValidate(true)
    onBlurProp?.(e)
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (Utils.keys.isEscape(e)) {
      e.currentTarget.blur()
    }
    onKeyDownProp?.(e)
  }

  const invalid = shouldValidate && !isValid
  const success = isValid && showSuccess
  const sizeClassName = size ? sizeClassNames[size] : ''
  const containerClassName = cn(
    {
      'focused': isFocused,
      'input-container': true,
      'input-underline': underline,
      invalid,
      'password': typeProp === 'password',
      'search': search,
      success,
    },
    className,
  )
  const innerClassName = cn(
    { 'input': true, 'text-center': centered },
    inputClassName,
    sizeClassName,
  )
  const iconWidth = size ? iconWidthBySize[size] : undefined

  return (
    <div className={containerClassName}>
      <input
        ref={inputRef}
        {...rest}
        onChange={onChange}
        onFocus={onFocus}
        onKeyDown={onKeyDown}
        type={type}
        onBlur={onBlur}
        value={value}
        className={innerClassName}
        disabled={disabled}
        autoComplete={enableAutoComplete ?? autocomplete}
      />
      {typeProp === 'password' && (
        <span
          className={cn(
            { 'clickable': true, 'input-icon-right': true },
            sizeClassName,
          )}
          onClick={() => {
            if (!disabled) {
              setType(type === 'password' ? 'text' : 'password')
            }
          }}
        >
          <Icon
            name={type === 'password' ? 'eye' : 'eye-off'}
            fill={invalid ? colorIconDanger : undefined}
            width={iconWidth}
          />
        </span>
      )}
      {search && (
        <span className={cn({ 'input-icon-right': true }, sizeClassName)}>
          <Icon name='search' width={iconWidth} />
        </span>
      )}
    </div>
  )
}

Input.displayName = 'Input'

export default Input
