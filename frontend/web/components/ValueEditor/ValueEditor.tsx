import React, { FC, ReactNode, useEffect, useId, useState } from 'react'
import cx from 'classnames'

import FieldLabel from 'components/base/forms/FieldLabel'
import Highlight from 'components/Highlight'
import { FlagsmithValue } from 'common/types/responses'

import CopyValueButton from './components/CopyValueButton'
import LanguageSelector from './components/LanguageSelector'
import { ValueEditorLanguage } from './types'

export interface ValueEditorProps {
  className?: string
  'data-test'?: string
  disabled?: boolean
  // Renders the field's label and wires it to the editor. Callers used to
  // render their own, which is why three different label treatments grew up
  // around this component and none of them named the editor.
  label?: ReactNode
  labelTooltip?: string
  language?: ValueEditorLanguage
  name?: string
  onBlur?: () => void
  onChange?: (value: string) => void
  // placeholder and readOnly only reach the editor under E2E, which swaps
  // Highlight for a plain textarea. Highlight renders its own
  // 'Enter a value...' and stops accepting input while disabled.
  placeholder?: string
  readOnly?: boolean
  value?: FlagsmithValue
}

const ValueEditor: FC<ValueEditorProps> = ({
  className,
  disabled,
  label,
  labelTooltip,
  language: languageProp,
  name,
  onBlur,
  onChange,
  placeholder,
  readOnly,
  value,
  ...rest
}) => {
  const [language, setLanguage] = useState<ValueEditorLanguage>('txt')
  const labelId = useId()
  const editorId = useId()
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
  // copy too. It now lives inside the editor, so repeat the condition.
  const showControls = !disabled

  return (
    <div
      className={cx(
        'value-editor',
        { 'disabled': disabled, 'light': language === 'txt' },
        className,
      )}
    >
      {(label || showControls) && (
        <div className='value-editor__header'>
          {label && (
            <FieldLabel id={labelId} tooltip={labelTooltip}>
              {label}
            </FieldLabel>
          )}
          {showControls && (
            <LanguageSelector
              language={language}
              onChange={setLanguage}
              value={text}
            />
          )}
        </div>
      )}

      <div className='value-editor__field'>
        {showControls && <CopyValueButton value={text} />}

        {E2E ? (
          <textarea
            aria-labelledby={label ? labelId : undefined}
            data-test={rest['data-test']}
            disabled={disabled}
            id={editorId}
            name={name}
            onBlur={onBlur}
            onChange={(e) => onChange?.(e.target.value)}
            placeholder={placeholder}
            readOnly={readOnly}
            value={text}
          />
        ) : (
          <Highlight
            aria-labelledby={label ? labelId : undefined}
            data-test={E2E ? rest['data-test'] : ''}
            disabled={disabled}
            id={editorId}
            onChange={disabled ? null : onChange}
            onBlur={disabled ? null : onBlur}
            className={language}
          >
            {text}
          </Highlight>
        )}
      </div>
    </div>
  )
}

export default ValueEditor
