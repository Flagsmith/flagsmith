import React from 'react'

export interface OptionType {
  enabled?: boolean
  label: string
  value: string
}

export interface GroupedOptionType {
  label: React.ReactNode
  options: OptionType[]
}

interface SearchableDropdownProps {
  placeholder: string
  options: OptionType[] | GroupedOptionType[]
  value: string | number | null
  dataTest?: string
  isSearchable?: boolean
  displayedLabel?: string
  noOptionsMessage?: string
  maxMenuHeight?: number
  onBlur?: (e: OptionType) => void
  onInputChange?: (e: string, metadata: any) => void
  onChange?: (e: OptionType) => void
}

const SearchableDropdown: React.FC<SearchableDropdownProps> = ({
  dataTest,
  displayedLabel,
  isSearchable,
  maxMenuHeight,
  noOptionsMessage,
  onBlur,
  onChange,
  onInputChange,
  options,
  placeholder,
  value,
}) => {
  return (
    <>
      <Select
        data-test={dataTest}
        placeholder={placeholder}
        value={value ? { label: displayedLabel || value, value: value } : null}
        onBlur={onBlur}
        isSearchable={isSearchable}
        onInputChange={onInputChange}
        onChange={onChange}
        options={options}
        maxMenuHeight={maxMenuHeight}
        {...(noOptionsMessage
          ? { noOptionsMessage: () => noOptionsMessage }
          : {})}
      />
    </>
  )
}

export default SearchableDropdown
