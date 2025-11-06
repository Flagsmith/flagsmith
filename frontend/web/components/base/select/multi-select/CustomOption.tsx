import { OptionProps } from 'react-select/lib/components/Option'
import { MultiSelectOption } from './MultiSelect'
import Icon from 'components/Icon'

export const CustomOption = ({
    children,
    color,
    ...props
  }: OptionProps<MultiSelectOption> & { color?: string }) => {
    return (
      <div
        {...props.innerProps}
        role="option"
        aria-selected={props.isSelected}
        aria-disabled={props.isDisabled}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          cursor: props.isDisabled ? 'not-allowed' : 'pointer',
          backgroundColor: props.isFocused ? '#f0f0f0' : 'transparent',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', flex: 1, wordWrap: 'break-word', minWidth: 0, gap: '8px' }}>
          {color && (
            <div
              aria-hidden="true"
              style={{
                backgroundColor: color,
                borderRadius: '2px',
                flexShrink: 0,
                height: '12px',
                width: '12px',
              }}
            />
          )}
          <span style={{ flex: 1, wordWrap: 'break-word', minWidth: 0 }}>{children}</span>
        </div>
        {props.isSelected && (
          <div aria-hidden="true">
            <Icon width={14} name='checkmark-circle' fill='#6837fc' />
          </div>
        )}
      </div>
    )
  }