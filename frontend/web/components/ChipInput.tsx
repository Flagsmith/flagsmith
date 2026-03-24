import React, { FC, FormEventHandler, KeyboardEvent, useRef, useState } from 'react'
import Utils from 'common/utils/utils'
import { filter } from 'lodash'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

type ChipInputType = {
  placeholder?: string
  value?: string[]
  onChange: (v: string[]) => void
}

const ChipInput: FC<ChipInputType> = ({ onChange, placeholder, value }) => {
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const addChips = (text: string) => {
    const currentValue = value || []
    const split = filter(
      text.split(/[ ,;]/),
      (v) => v !== ' ' && v !== ',' && v !== ';' && v !== '',
    )
    if (split.length) {
      onChange(currentValue.concat(split))
    }
    setInputValue('')
  }

  const onChangeText: FormEventHandler<HTMLInputElement> = (e) => {
    const v = Utils.safeParseEventValue(e)
    if (v.search(/[ ,]/) !== -1) {
      addChips(v)
    } else {
      setInputValue(v)
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (inputValue.trim()) {
        addChips(inputValue)
      }
    } else if (e.key === 'Backspace' && !inputValue && value?.length) {
      onChange(Utils.removeElementFromArray(value, value.length - 1))
    }
  }

  const onBlur = () => {
    if (inputValue.trim()) {
      addChips(inputValue)
    }
  }

  const onDelete = (index: number) => {
    const v = value || []
    onChange(Utils.removeElementFromArray(v, index))
  }

  return (
    <div
      className='mui-root'
      onClick={() => inputRef.current?.focus()}
      role='presentation'
    >
      {value?.map((chip, index) => (
        <span
          key={index}
          className='chip'
          role='button'
          tabIndex={0}
        >
          <span>{chip}</span>
          <span
            className='chip-icon ion'
            onClick={(e) => {
              e.stopPropagation()
              onDelete(index)
            }}
            role='button'
            tabIndex={0}
          >
            <IonIcon icon={close} />
          </span>
        </span>
      ))}
      <input
        ref={inputRef}
        className='chip-input'
        placeholder={!value?.length ? placeholder : ''}
        value={inputValue}
        onChange={onChangeText}
        onKeyDown={onKeyDown}
        onBlur={onBlur}
      />
    </div>
  )
}

export default ChipInput
