import React, { useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import Icon from 'components/Icon'
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
  const handleChange = () => {
    onChange(!checked)
  }

  return (
    <>
      <input id={idRef.current} type='checkbox' />
      <label
        onClick={handleChange}
        className='mb-0'
        htmlFor={idRef.current}
        style={{ display: 'inline' }}
      >
        <span className='checkbox mr-2'>
          {checked && <Icon name='checkmark-square' />}
        </span>
        {label}
      </label>
    </>
  )
}

export default Checkbox
