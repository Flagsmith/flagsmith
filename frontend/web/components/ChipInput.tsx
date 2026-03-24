import React, { FC, FormEventHandler, useState } from 'react'
import TheInput from 'material-ui-chip-input'
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
  const onChangeText: FormEventHandler = (e) => {
    const v = Utils.safeParseEventValue(e)
    const currentValue = value || []
    if (v.search(/[ ,]/) !== -1) {
      //delimit when detecting one of the following characters
      const split = filter(
        v.split(/[ ,;]/),
        (v) => v !== ' ' && v !== ',' && v !== ';' && v !== '',
      )
      setInputValue('')
      onChange(currentValue.concat(split))
    } else {
      setInputValue(v)
    }
  }

  const onDelete = (_: any, index: number) => {
    const v = value || []
    onChange(Utils.removeElementFromArray(v, index))
  }

  const onSubmit = (chip: string) => {
    if (chip) {
      onChange((value || []).concat([chip]))
    }
    setInputValue('')
    return true
  }

  return (
    <TheInput
      fullWidth
      placeholder={placeholder}
      blurBehavior='add'
      onChangeCapture={onChangeText}
      value={value}
      inputValue={inputValue}
      onDelete={onDelete}
      onBeforeAdd={onSubmit}
      onChange={onChange}
      classes={{
        chip: 'chip',
        root: 'mui-root',
      }}
      chipRenderer={({ className, handleClick, handleDelete, value }, key) => (
        <span
          key={key}
          className={className}
          onClick={handleClick}
          role='button'
          tabIndex={0}
        >
          <span>{value}</span>
          <span
            className='chip-icon ion'
            onClick={handleDelete}
            role='button'
            tabIndex={0}
          >
            <IonIcon icon={close} />
          </span>
        </span>
      )}
    />
  )
}

export default ChipInput
