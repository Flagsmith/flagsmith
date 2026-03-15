import React, {
  FC,
  FormEventHandler,
  KeyboardEventHandler,
  useState,
} from 'react'
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

  const onChangeText: FormEventHandler = (e) => {
    const v = Utils.safeParseEventValue(e)
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
    }
  }

  const onBlur = () => {
    if (inputValue.trim()) {
      addChips([inputValue.trim()])
    }
  }

  const onDelete = (index: number) => {
    const v = value || []
    onChange(Utils.removeElementFromArray(v, index))
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
              <IonIcon icon={close} />
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
