import { OptionProps } from 'react-select/lib/components/Option'
import { MultiSelectOption } from './MultiSelect'
import Icon from 'components/Icon'
import { useEffect, useRef } from 'react'

export const CustomOption = ({
  children,
  color,
  ...props
}: OptionProps<MultiSelectOption> & { color?: string }) => {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (props.isFocused && ref.current) {
      ref.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      })
    }
  }, [props.isFocused])

  return (
    <div
      ref={ref}
      {...props.innerProps}
      role='option'
      aria-selected={props.isSelected}
      aria-disabled={props.isDisabled}
      style={{
        alignItems: 'center',
        backgroundColor: props.isFocused ? '#f0f0f0' : 'transparent',
        cursor: props.isDisabled ? 'not-allowed' : 'pointer',
        display: 'flex',
        gap: '8px',
        justifyContent: 'space-between',
        padding: '8px 12px',
      }}
    >
      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          flex: 1,
          gap: '8px',
          minWidth: 0,
          wordWrap: 'break-word',
        }}
      >
        {color && (
          <div
            aria-hidden='true'
            style={{
              backgroundColor: color,
              borderRadius: '2px',
              flexShrink: 0,
              height: '12px',
              width: '12px',
            }}
          />
        )}
        <span style={{ flex: 1, minWidth: 0, wordWrap: 'break-word' }}>
          {children}
        </span>
      </div>
      {props.isSelected && (
        <div aria-hidden='true'>
          <Icon width={14} name='checkmark-circle' fill='#6837fc' />
        </div>
      )}
    </div>
  )
}
