import React, { FC, useEffect, useState } from 'react' // we need this to make JSX compile
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'

import InputGroup from './base/forms/InputGroup'
type RegexTesterType = {
  regex: string
  onChange: (newRegex: string) => void
}

const RegexTester: FC<RegexTesterType> = ({
  onChange,
  regex: defaultRegex,
}) => {
  const [exampleText, setExampleText] = useState('')
  const [regex, setRegex] = useState(defaultRegex)
  let valid = false
  try {
    valid = !!exampleText.match(new RegExp(regex))
  } catch (e) {}
  useEffect(() => {
    setTimeout(() => {
      document.getElementById('regex')?.focus()
    }, 500)
  }, [])
  const forceSelectionRange = (e: InputEvent) => {
    const input = e.currentTarget as HTMLInputElement
    setTimeout(() => {
      const range = input.selectionStart
      if (range === input.value.length) {
        input.setSelectionRange(input.value.length - 1, input.value.length - 1)
      }
    }, 0)
  }
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onChange(regex)
        closeModal()
      }}
    >
      <InputGroup
        title='Regular Expression'
        value={regex}
        autoValidate
        inputProps={{
          className: 'full-width',
          onClick: forceSelectionRange,
          onKeyUp: forceSelectionRange,
          showSuccess: true,
        }}
        onChange={(e: InputEvent) => {
          let newRegex = Utils.safeParseEventValue(e).replace('$', '')
          if (!newRegex.startsWith('^')) {
            newRegex = `^${newRegex}`
          }
          if (!newRegex.endsWith('$')) {
            newRegex = `${newRegex}$`
          }
          setRegex(newRegex)
        }}
      />
      <InputGroup
        id='regex'
        title='Test Input'
        value={exampleText}
        autoValidate
        inputProps={{
          autoValidate: true,
          className: 'full-width',
          showSuccess: true,
        }}
        isValid={valid}
        onChange={(e: InputEvent) => {
          setExampleText(Utils.safeParseEventValue(e))
        }}
      />

      <div className='mt-4 text-right'>
        <Button
          onClick={() => {
            closeModal()
          }}
          type='button'
        >
          Cancel
        </Button>
        <Button className='ml-2' type='submit'>
          Save RegEx
        </Button>
      </div>
    </form>
  )
}

export default RegexTester
