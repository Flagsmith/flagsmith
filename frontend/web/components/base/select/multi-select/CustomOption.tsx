
import { OptionProps } from 'react-select/lib/components/Option'
import { MultiSelectOption } from './MultiSelect'

export const CustomOption = ({
    children,
    color,
    ...props
  }: OptionProps<MultiSelectOption> & { color?: string }) => {
    return (
      <div
        {...props.innerProps}
        className={`d-flex align-items-center p-2 ${
          props.isFocused ? 'bg-light' : ''
        }`}
        style={{ cursor: 'pointer' }}
      >
        {color && (
          <div
            style={{
              backgroundColor: color,
              borderRadius: '2px',
              flexShrink: 0,
              height: '12px',
              marginRight: '8px',
              width: '12px',
            }}
          />
        )}
        <span>{children}</span>
      </div>
    )
  }