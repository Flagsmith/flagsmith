import React, { useState } from 'react'
import Checkbox from './Checkbox'

interface CheckboxGroupItem {
  label: string
  value: string
}

interface CheckboxGroupProps {
  items: CheckboxGroupItem[]
  selectedValues: string[]
  onChange: (selected: string[]) => void
}

const CheckboxGroup: React.FC<CheckboxGroupProps> = ({
  items,
  onChange,
  selectedValues,
}) => {
  const handleCheckboxChange = (value: string, checked: boolean) => {
    const newSelectedValues = checked
      ? [...selectedValues, value]
      : selectedValues.filter((v) => v !== value)

    onChange(newSelectedValues)
  }

  return (
    <div className='d-flex flex-column gap-3 mt-1'>
      {items.map(({ label, value }) => (
        <Checkbox
          key={value}
          label={label}
          checked={selectedValues.includes(value)}
          onChange={(checked) => handleCheckboxChange(value, checked)}
        />
      ))}
    </div>
  )
}

export default CheckboxGroup
