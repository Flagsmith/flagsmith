import Icon from 'components/Icon'
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

export const GroupLabel = ({
  groupName,
  tooltipText,
}: {
  groupName: string
  tooltipText?: string
}) => {
  return (
    <div className='d-flex align-items-center gap-1'>
      <div>{groupName}</div>
      {tooltipText && (
        <Tooltip
          title={
            <h5 className='mb-1 cursor-pointer'>
              <Icon name='info-outlined' height={16} width={16} />
            </h5>
          }
          place='right'
        >
          {tooltipText}
        </Tooltip>
      )}
    </div>
  )
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
  onBlur?: (e: OptionType | null) => void
  onInputChange?: (e: string, metadata: any) => void
  onChange?: (e: OptionType) => void
  isMulti?: boolean
  isClearable?: boolean
  components?: any
}

const SearchableDropdown: React.FC<SearchableDropdownProps> = ({
  components,
  dataTest,
  displayedLabel,
  isClearable = false,
  isMulti,
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
      isMulti={isMulti}
      {...(noOptionsMessage
        ? { noOptionsMessage: () => noOptionsMessage }
        : {})}
      isClearable={isClearable}
      className={`react-select ${
        isClearable && value ? 'clearable-dropdown' : ''
      }`}
      components={components}
    />
  )
}

export default SearchableDropdown
