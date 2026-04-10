import { MultiValueProps } from 'react-select'
import { MultiSelectOption } from './MultiSelect'

export const CustomMultiValue = ({
  color,
  data,
  removeProps,
}: MultiValueProps<MultiSelectOption> & { color?: string }) => {
  return (
    <div
      className='d-flex align-items-center gap-1 rounded-sm text-white overflow-hidden fs-small'
      style={{
        backgroundColor: color,
        maxHeight: 24,
        maxWidth: 150,
        padding: '2px 6px',
      }}
    >
      <span className='text-nowrap overflow-hidden text-truncate'>
        {data.label}
      </span>
      <button
        {...removeProps}
        className='btn-close btn-close-white p-0 border-0'
        style={{ fontSize: 10 }}
        aria-label={`Remove ${data.label}`}
      />
    </div>
  )
}
