import { MultiSelectOption } from "./MultiSelect"
import { MultiValueProps } from "react-select/lib/components/MultiValue"

export const InlineMultiValue = (props: MultiValueProps<MultiSelectOption>) => {
    const { data } = props
    const selectedOptions = props.getValue() as MultiSelectOption[]
    const currentIndex = selectedOptions.findIndex((opt) => opt.value === data.value)

    // Only render on the first item to avoid duplicates
    if (currentIndex !== 0) return null

    const formattedText = selectedOptions.length === 1
      ? selectedOptions[0].label
      : selectedOptions.length === 2
      ? `${selectedOptions[0].label} and ${selectedOptions[1].label}`
      : `${selectedOptions.slice(0, -1).map((opt) => opt.label).join(', ')} and ${selectedOptions[selectedOptions.length - 1].label}`

    return (
      <div style={{
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        maxWidth: '100%',
        fontWeight: '500',
      }}>
        {formattedText}
      </div>
    )
  }