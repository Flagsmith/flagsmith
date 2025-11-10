import classNames from 'classnames'
import React, { FC } from 'react'
import { MultiValueProps } from 'react-select/lib/components/MultiValue'
import { OptionProps } from 'react-select/lib/components/Option'

import { CustomMultiValue } from './CustomMultiValue'
import { CustomOption } from './CustomOption'
import { InlineMultiValue } from './InlineMultiValue'

export interface MultiSelectOption {
  label: string
  value: string
}

export interface MultiSelectProps {
  selectedValues: string[]
  onSelectionChange: (selectedValues: string[]) => void
  options: MultiSelectOption[]
  colorMap?: Map<string, string>
  label?: string
  placeholder?: string
  className?: string
  disabled?: boolean
  size?: 'small' | 'default' | 'large'
  hideSelectedOptions?: boolean
  inline?: boolean
}

export const MultiSelect: FC<MultiSelectProps> = ({
  className = '',
  colorMap,
  disabled = false,
  label,
  onSelectionChange,
  options,
  placeholder = 'Select options...',
  selectedValues,
  size = 'default',
  hideSelectedOptions = true,
  inline = false,
}) => {
  return (
    <div className={classNames(
        className,
        label ? `d-flex flex-column gap-2` : ''
      )}>
      {label && <label>{label}</label>}
      <Select
        isMulti
        hideSelectedOptions={hideSelectedOptions}
        closeMenuOnSelect={false}
        placeholder={placeholder}
        isDisabled={disabled}
        size={size}
        onChange={(selectedOptions: MultiSelectOption[] | null) => {
          onSelectionChange(selectedOptions ? selectedOptions.map((opt: MultiSelectOption) => opt.value) : [])
        }}
        components={{
          ...(inline ? {
            MultiValue: (props: MultiValueProps<MultiSelectOption>) => (
              <InlineMultiValue {...props} />
            ),
          } : {
            MultiValue: (props: MultiValueProps<MultiSelectOption>) => (
              <CustomMultiValue
                {...props}
                color={colorMap?.get(props.data.value) || '#5D6D7E'}
              />
            ),
          }),
          Option: (props: OptionProps<MultiSelectOption>) => (
            <CustomOption
              {...props}
              color={colorMap?.get(props.data.value)}
            />
          ),
        }}
        value={selectedValues.map((value) => ({
          label: options.find((opt) => opt.value === value)?.label || value,
          value,
        }))}
        options={options}
        className='react-select react-select__extensible w-100'
        styles={{
          control: (base: any) => ({
            ...base,
            cursor: 'pointer',
          }),
          multiValue: (base: any) => ({
            ...base,
            flexShrink: 0,
            margin: '2px',
          }),
          valueContainer: (base: any) => ({
            ...base,
            flexWrap: 'nowrap',
            gap: '2px',
            paddingBottom: '6px',
            paddingTop: '6px',
            flex: 1,
            overflow: 'hidden',
          }),
          input: (base: any) => ({
            ...base,
            margin: 0,
            paddingBottom: 0,
            paddingTop: 0,
          }),
          singleValue: (base: any) => ({
            ...base,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }),
        }}
      />
    </div>
  )
}
