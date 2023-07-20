import React, { FC, TextareaHTMLAttributes, useState } from 'react'
import cn from 'classnames'

type TextareaType = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  isValid?: boolean
  className?: string
}

const TextArea: FC<TextareaType> = ({
  value,
  onChange,
  isValid = true,
  className = '',
  onBlur,
  ...rest
}) => {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const [shouldValidate, setShouldValidate] = useState(!!value)
  const invalid = shouldValidate && !isValid
  const MIN_TEXTAREA_HEIGHT = 50

  React.useLayoutEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '0'
      textareaRef.current.style.height = `${Math.max(
        textareaRef.current.scrollHeight,
        MIN_TEXTAREA_HEIGHT,
      )}px`
    }
  }, [value])

  return (
    <textarea
      {...rest}
      onChange={onChange}
      ref={textareaRef}
      value={value}
      onBlur={(e) => {
        setShouldValidate(true)
        onBlur && onBlur(e)
      }}
      className={cn(
        {
          invalid,
        },
        'textarea-container',
        className,
      )}
    />
  )
}

export default TextArea
