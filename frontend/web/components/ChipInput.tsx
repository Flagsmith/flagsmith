import React, {
  ChangeEventHandler,
  FC,
  KeyboardEventHandler,
  useState,
} from 'react'
import { filter } from 'lodash'
import Icon from './icons/Icon'

type ChipInputType = {
  placeholder?: string
  value?: string[]
  onChange: (v: string[]) => void
}

const ChipInput: FC<ChipInputType> = ({ onChange, placeholder, value }) => {
  const [inputValue, setInputValue] = useState('')

  const addChips = (chips: string[]) => {
    const currentValue = value || []
    const filtered = filter(
      chips,
      (v) => v !== ' ' && v !== ',' && v !== ';' && v !== '',
    )
    if (filtered.length) {
      onChange(currentValue.concat(filtered))
    }
    setInputValue('')
  }

  const onChangeText: ChangeEventHandler<HTMLInputElement> = (e) => {
    const v = e.currentTarget.value
    if (v.search(/[ ,]/) !== -1) {
      addChips(v.split(/[ ,;]/))
    } else {
      setInputValue(v)
    }
  }

  const onKeyDown: KeyboardEventHandler = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (inputValue.trim()) {
        addChips([inputValue.trim()])
      }
    } else if (e.key === 'Backspace' && !inputValue && value?.length) {
      onDelete(value.length - 1)
    }
  }

  const onBlur = () => {
    if (inputValue.trim()) {
      addChips([inputValue.trim()])
    }
  }

  const onDelete = (index: number) => {
    const v = value || []
    onChange(v.filter((_, i) => i !== index))
  }

  return (
    <div className='chip-input'>
      <div className='chip-input__chips'>
        {value?.map((chip, index) => (
          <span key={`${chip}-${index}`} className='chip'>
            <span>{chip}</span>
            <span
              className='chip-icon ion'
              onClick={() => onDelete(index)}
              role='button'
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onDelete(index)
              }}
            >
              <Icon name='close' width={16} height={16} fill='currentColor' />
            </span>
          </span>
        ))}
        <input
          className='chip-input__input'
          placeholder={!value?.length ? placeholder : ''}
          value={inputValue}
          onChange={onChangeText}
          onKeyDown={onKeyDown}
          onBlur={onBlur}
        />
      </div>
    </div>
  )
}

export default ChipInput
