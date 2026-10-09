import React, { FC, ReactNode } from 'react'
import Input from 'components/base/forms/Input'
import FieldError from 'components/base/forms/FieldError'

type WarehouseConfigFieldProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  hint?: ReactNode
  error?: string | false
  disabled?: boolean
  type?: string
  autoComplete?: string
}

const WarehouseConfigField: FC<WarehouseConfigFieldProps> = ({
  autoComplete,
  disabled,
  error,
  hint,
  id,
  label,
  onChange,
  placeholder,
  type,
  value,
}) => {
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const describedBy = [error && errorId, hint && hintId]
    .filter(Boolean)
    .join(' ')
  return (
    <div className='wh-config-form__field'>
      <label
        className='wh-config-form__label fs-caption text-secondary'
        htmlFor={id}
      >
        {label}
      </label>
      <Input
        id={id}
        value={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          onChange(e.target.value)
        }
        placeholder={placeholder}
        disabled={disabled}
        type={type}
        autoComplete={autoComplete}
        aria-invalid={!!error}
        aria-describedby={describedBy || undefined}
      />
      <FieldError id={errorId} error={error} />
      {hint && (
        <span id={hintId} className='fs-captionXSmall text-tertiary'>
          {hint}
        </span>
      )}
    </div>
  )
}

WarehouseConfigField.displayName = 'WarehouseConfigField'
export default WarehouseConfigField
