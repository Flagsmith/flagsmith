import { MultiSelectOption } from './MultiSelect'
import { MultiValueProps } from 'react-select/lib/components/MultiValue'

export const InlineMultiValue = (props: MultiValueProps<MultiSelectOption>) => {
  const { data } = props
  const selectedOptions = props.getValue() as MultiSelectOption[]
  const currentIndex = selectedOptions.findIndex(
    (opt) => opt.value === data.value,
  )

  if (currentIndex !== 0) return null

  let formattedText: string
  if (selectedOptions.length === 1) {
    formattedText = selectedOptions[0].label
  } else if (selectedOptions.length === 2) {
    formattedText = `${selectedOptions[0].label} and ${selectedOptions[1].label}`
  } else {
    const allButLast = selectedOptions
      .slice(0, -1)
      .map((opt) => opt.label)
      .join(', ')
    const last = selectedOptions[selectedOptions.length - 1].label
    formattedText = `${allButLast} and ${last}`
  }

  return (
    <div
      title={formattedText}
      style={{
        fontWeight: '500',
        maxWidth: '100%',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}
    >
      {formattedText}
    </div>
  )
}
