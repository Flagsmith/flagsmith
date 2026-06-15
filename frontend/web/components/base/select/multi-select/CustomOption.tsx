import { OptionProps } from 'react-select'
import { MultiSelectOption } from './MultiSelect'
import Icon from 'components/icons/Icon'
import ColorSwatch from 'components/ColorSwatch'
import { useEffect, useRef } from 'react'
import classNames from 'classnames'

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
      className={classNames(
        'd-flex align-items-center justify-content-between gap-2 px-3 py-2 cursor-pointer',
        {
          'bg-surface-hover': props.isFocused,
          'cursor-not-allowed': props.isDisabled,
        },
      )}
    >
      <div className='d-flex align-items-center flex-fill gap-2 overflow-hidden'>
        {color && <ColorSwatch color={color} />}
        <span className='flex-fill overflow-hidden text-break'>{children}</span>
      </div>
      {props.isSelected && (
        <span className='icon-action' aria-hidden='true'>
          <Icon width={14} name='checkmark-circle' />
        </span>
      )}
    </div>
  )
}
