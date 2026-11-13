import React, { useRef } from 'react'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'

interface CheckboxProps {
  label: string
  onChange: (value: boolean) => void
  checked: boolean
  id?: string
}

const Checkbox: React.FC<CheckboxProps> = ({
  checked,
  id,
  label,
  onChange,
}) => {
  const idRef = useRef(id || Utils.GUID())

  return (
    <>
      <input
        id={idRef.current}
        className='checkbox-input'
        type='checkbox'
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <label
        className='mb-0 user-select-none d-inline cursor-pointer'
        htmlFor={idRef.current}
      >
        <span className='checkbox mr-2' aria-hidden>
          {checked && <Icon name='checkmark-square' />}
        </span>
        {label}
      </label>
    </>
  )
}

export default Checkbox
