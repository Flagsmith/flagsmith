import React, { forwardRef, useEffect, useState } from 'react'
import classNames from 'classnames'

type GhostInputProps = {
  value?: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onBlur?: () => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void
  placeholder?: string
  className?: string
  width?: number
  'aria-label'?: string
}

const GhostInput = forwardRef<HTMLInputElement, GhostInputProps>(
  ({ 
    'aria-label': ariaLabel, 
    className, 
    onBlur, 
    onChange, 
    onKeyDown, 
    placeholder = '',
    value,
  }, ref) => {
  const [width, setWidth] = useState(5);
  
  useEffect(() => {
    setWidth(value?.length || 5)
  }, [value])

    return (
      <input
        ref={ref}
        className={classNames('fw-normal', className, { 
          'text-muted': !value 
        })}
        value={value}
        placeholder={placeholder}
        onChange={onChange}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        role='textbox'
        aria-label={ariaLabel}
        style={{
          background: 'transparent',
          border: 'none',
          boxShadow: 'none',
          color: 'inherit',
          cursor: 'text',
          fontFamily: 'inherit',
          fontSize: 'inherit',
          margin: 0,
          outline: 'none',
          padding: 0,
          width: width ? `${width}ch` : 'auto'
        }}
      />
    )
  }
)

GhostInput.displayName = 'GhostInput'

export default GhostInput
