import classNames from 'classnames'
import React from 'react'
import { MultiValueProps } from 'react-select/lib/components/MultiValue'

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
}

const CustomMultiValue = ({
  color,
  data,
  removeProps,
}: MultiValueProps<MultiSelectOption> & { color?: string }) => {
  return (
    <div
      className='d-flex align-items-center'
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
        className='mr-1'
        style={{
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {data.label}
      </span>
      <span
        onClick={() => removeProps?.onClick?.(data)}
        style={{
          cursor: 'pointer',
          fontSize: '14px',
          lineHeight: '1',
        }}
      >
        ×
      </span>
    </div>
  )
}

const CustomOption = ({
  children,
  color,
  ...props
}: any & { color?: string }) => {
  return (
    <div
      {...props.innerProps}
      className={`d-flex align-items-center p-2 ${
        props.isFocused ? 'bg-light' : ''
      }`}
      style={{ cursor: 'pointer' }}
    >
      {color && (
        <div
          style={{
            backgroundColor: color,
            borderRadius: '2px',
            flexShrink: 0,
            height: '12px',
            marginRight: '8px',
            width: '12px',
          }}
        />
      )}
      <span>{children}</span>
    </div>
  )
}

const MultiSelect: React.FC<MultiSelectProps> = ({
  className = '',
  colorMap,
  disabled = false,
  label,
  onSelectionChange,
  options,
  placeholder = 'Select options...',
  selectedValues,
  size = 'default',
}) => {
  return (
    <div className={classNames(
        className,
        label ? `d-flex flex-column gap-2` : ''
      )}>
      {label && <label>{label}</label>}
      <Select
        isMulti
        closeMenuOnSelect={false}
        placeholder={placeholder}
        isDisabled={disabled}
        size={size}
        onChange={(selectedOptions: any) => {
          const values = selectedOptions
            ? selectedOptions.map((opt: any) => opt.value)
            : []
          onSelectionChange(values)
        }}
        components={{
          MultiValue: (props: MultiValueProps<MultiSelectOption>) => (
            <CustomMultiValue
              {...props}
              className={classNames(props.className, 'h-[24px]')}
              color={colorMap?.get(props.data.value) || '#5D6D7E'}
            />
          ),
          ...(colorMap ? {Option: (props: any) => <CustomOption
            {...props}
            color={colorMap.get(props.data.value)}
          />} : {}),
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
            flexWrap: 'wrap',
            gap: '4px',
            overflow: 'visible',
            paddingBottom: '6px',
            paddingTop: '6px',
          }),
        }}
      />
    </div>
  )
}

export default MultiSelect
