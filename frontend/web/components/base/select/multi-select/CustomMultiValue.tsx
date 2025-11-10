import { MultiValueProps } from 'react-select/lib/components/MultiValue'
import { MultiSelectOption } from './MultiSelect'

export const CustomMultiValue = ({
    color,
    data,
    removeProps,
  }: MultiValueProps<MultiSelectOption> & { color?: string }) => {
    return (
      <div
        className='d-flex align-items-center gap-x-1'
        style={{
          backgroundColor: color,
          borderRadius: '4px',
          color: 'white',
          fontSize: '12px',
          maxWidth: '150px',
          overflow: 'hidden',
          padding: '2px 6px',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          maxHeight: '24px'
        }}
      >
        <span
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {data.label}
        </span>
        <button
            {...removeProps}
            style={{
            cursor: 'pointer',
            fontSize: '14px',
            lineHeight: '1',
            backgroundColor: 'transparent',
            border: 'none',
            padding: 0,
            margin: 0,
            color: 'white',
          }}
        >
          ×
        </button>
      </div>
    )
  }