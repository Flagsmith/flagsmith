import React from 'react'
import ReactMarkdown from 'react-markdown'
import Icon from 'components/Icon'

interface CheckboxProps {
  label: string
  onChange: (value: boolean) => void
  checked: boolean
}

const Checkbox: React.FC<CheckboxProps> = ({ checked, label, onChange }) => {
  const handleChange = () => {
    onChange(!checked)
  }

  return (
    <>
      <input type='checkbox' />
      <label
        onClick={handleChange}
        className='mb-0'
        htmlFor='mailinglist'
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
