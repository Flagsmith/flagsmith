import React, { useLayoutEffect, useRef, useState } from 'react'
import classNames from 'classnames'
import './GhostInput.scss'

type GhostInputProps = {
  value?: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onBlur?: () => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void
  placeholder: string
  className?: string
  maxLength?: number
  ref?: React.Ref<HTMLInputElement>
  'aria-label'?: string
}

const GhostInput = ({
  'aria-label': ariaLabel,
  className,
  maxLength = 100,
  onBlur,
  onChange,
  onKeyDown,
  placeholder = '',
  ref,
  value,
}: GhostInputProps) => {
  const spanRef = useRef<HTMLSpanElement>(null)
  const [inputWidth, setInputWidth] = useState(5)

  // Auto-size the field to its content by measuring a hidden span that mirrors
  // the text and font. +2px leaves room for the caret so the last character
  // isn't clipped. useLayoutEffect (not useEffect) so the width is committed
  // before paint - otherwise fast typing paints a too-narrow frame first and
  // the trailing letters flicker as the box catches up.
  useLayoutEffect(() => {
    if (spanRef.current) {
      setInputWidth(spanRef.current.offsetWidth + 2)
    }
  }, [value])

  return (
    <span className='ghost-input d-inline-block position-relative'>
      <span
        ref={spanRef}
        className='ghost-input__sizer position-absolute m-0 p-0 border-0'
        aria-hidden
      >
        {value || placeholder}
      </span>
      <input
        ref={ref}
        maxLength={maxLength}
        className={classNames(
          'ghost-input__field fw-normal m-0 p-0 border-0 bg-transparent',
          className,
          { 'text-muted': !value },
        )}
        value={value}
        placeholder={placeholder}
        onChange={onChange}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        aria-label={ariaLabel}
        spellCheck={false}
        // Opt out of browser autofill + password-manager overlays (1Password,
        // LastPass); their icons would overlap the trailing edit pencil.
        autoComplete='off'
        data-1p-ignore
        data-lpignore='true'
        style={{ width: inputWidth }}
      />
    </span>
  )
}

export default GhostInput
