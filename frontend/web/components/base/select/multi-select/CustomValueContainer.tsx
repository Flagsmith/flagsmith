import React from 'react'
import { components } from 'react-select/lib/components'
import { ValueContainerProps } from 'react-select/lib/components/containers'
import { MultiSelectOption } from './MultiSelect'

export const CustomValueContainer = ({
  children,
  selectProps,
  ...props
}: ValueContainerProps<MultiSelectOption>) => {
  const { value } = selectProps
  const selectedOptions = (value || []) as MultiSelectOption[]

  const formattedText = formatSelectedLabels(selectedOptions)

  return (
    // @ts-ignore - react-select components.ValueContainer is a valid component
    <components.ValueContainer {...props} selectProps={selectProps}>
      {selectedOptions.length > 0 && (
        <div
          className='react-select__single-value'
          style={{
            position: 'absolute',
            maxWidth: 'calc(100% - 16px)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            top: '50%',
            transform: 'translateY(-50%)',
            boxSizing: 'border-box',
          }}
        >
          {formattedText}
        </div>
      )}
      <div style={{ opacity: selectedOptions.length > 0 ? 0 : 1 }}>
        {children}
      </div>
    </components.ValueContainer>
  )
}

function formatSelectedLabels(options: MultiSelectOption[]): string {
  if (options.length === 0) return ''
  if (options.length === 1) return options[0].label
  if (options.length === 2) return `${options[0].label} and ${options[1].label}`

  // 3+ items: "Item1, Item2, Item3 and Item4"
  const allButLast = options.slice(0, -1).map((opt) => opt.label).join(', ')
  const last = options[options.length - 1].label
  return `${allButLast} and ${last}`
}
