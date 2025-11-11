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
        maxHeight: '24px',
        maxWidth: '150px',
        overflow: 'hidden',
        padding: '2px 6px',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
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
          backgroundColor: 'transparent',
          border: 'none',
          color: 'white',
          cursor: 'pointer',
          fontSize: '14px',
          lineHeight: '1',
          margin: 0,
          padding: 0,
        }}
      >
        ×
      </button>
    </div>
  )
}
