import React, { forwardRef, useEffect, useRef, useState } from 'react'
import classNames from 'classnames'

type GhostInputProps = {
  value?: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onBlur?: () => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void
  placeholder: string
  className?: string
  width?: number
  'aria-label'?: string
}

const GhostInput = forwardRef<HTMLInputElement, GhostInputProps>(
  (
    {
      'aria-label': ariaLabel,
      className,
      onBlur,
      onChange,
      onKeyDown,
      placeholder = '',
      value,
    },
    ref,
  ) => {
    const spanRef = useRef<HTMLSpanElement>(null)
    const [inputWidth, setInputWidth] = useState(5)

    useEffect(() => {
      if (spanRef.current) {
        setInputWidth(spanRef.current.offsetWidth * 0.95)
      }
    }, [value])

    return (
      <div style={{ display: 'inline-block', position: 'relative' }}>
        <span
          ref={spanRef}
          style={{
            border: 0,
            fontFamily: 'inherit',
            fontSize: 'inherit',
            fontWeight: 'inherit',
            letterSpacing: 'inherit',
            lineHeight: 'inherit',
            margin: 0,
            padding: 0,
            position: 'absolute',
            visibility: 'hidden',
            whiteSpace: 'pre',
          }}
        >
          {value || placeholder}
        </span>
        <input
          ref={ref}
          maxLength={100}
          className={classNames('fw-normal', className, {
            'text-muted': !value,
          })}
          value={value}
          placeholder={placeholder}
          onChange={onChange}
          onBlur={onBlur}
          onKeyDown={onKeyDown}
          role='textbox'
          aria-label={ariaLabel}
          spellCheck={false}
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
            width: inputWidth,
          }}
        />
      </div>
    )
  },
)

GhostInput.displayName = 'GhostInput'

export default GhostInput
