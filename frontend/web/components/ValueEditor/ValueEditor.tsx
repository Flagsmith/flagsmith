import React, { FC, useEffect, useState } from 'react'
import cx from 'classnames'

import Highlight from 'components/Highlight'
import { FlagsmithValue } from 'common/types/responses'

import CopyValueButton from './components/CopyValueButton'
import LanguageSelector from './components/LanguageSelector'
import { ValueEditorLanguage } from './types'

export interface ValueEditorProps {
  className?: string
  'data-test'?: string
  disabled?: boolean
  language?: ValueEditorLanguage
  name?: string
  onBlur?: () => void
  onChange?: (value: string) => void
  // placeholder and readOnly only reach the editor under E2E, which swaps
  // Highlight for a plain textarea. Highlight renders its own
  // 'Enter a value...' and stops accepting input while disabled.
  placeholder?: string
  readOnly?: boolean
  onlyOneLang?: boolean
  value?: FlagsmithValue
}

const ValueEditor: FC<ValueEditorProps> = ({
  className,
  disabled,
  language: languageProp,
  name,
  onBlur,
  onChange,
  onlyOneLang,
  placeholder,
  readOnly,
  value,
  ...rest
}) => {
  const [language, setLanguage] = useState<ValueEditorLanguage>('txt')
  const text = value === undefined || value === null ? '' : `${value}`

  // Pick the initial language once: the caller's choice, overridden by JSON
  // when the value parses as an object.
  useEffect(() => {
    if (languageProp) {
      setLanguage(languageProp)
    }
    if (!value) return
    try {
      if (typeof JSON.parse(text) === 'object') {
        setLanguage('json')
      }
    } catch (e) {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Copy used to be the last item of the language row, so hiding that row hid
  // copy too. It now lives inside the editor, so repeat the conditions.
  const showCopy = !onlyOneLang && !disabled

  return (
    <div
      className={cx(
        'value-editor',
        { 'disabled': disabled, 'light': language === 'txt' },
        className,
      )}
    >
      {!onlyOneLang && (
        <LanguageSelector
          language={language}
          onChange={setLanguage}
          value={text}
        />
      )}

      {showCopy && <CopyValueButton value={text} />}

      {E2E ? (
        <textarea
          data-test={rest['data-test']}
          disabled={disabled}
          name={name}
          onBlur={onBlur}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder={placeholder}
          readOnly={readOnly}
          value={text}
        />
      ) : (
        <Highlight
          data-test={E2E ? rest['data-test'] : ''}
          disabled={disabled}
          onChange={disabled ? null : onChange}
          onBlur={disabled ? null : onBlur}
          className={language}
        >
          {text}
        </Highlight>
      )}
    </div>
  )
}

export default ValueEditor
