import React, { FC, ReactNode, useEffect, useId, useRef, useState } from 'react'
import cx from 'classnames'

import FieldLabel from 'components/base/forms/FieldLabel'
import Highlight from 'components/Highlight'
import { FlagsmithValue } from 'common/types/responses'

import CopyValueButton from './components/CopyValueButton'
import LanguageSelector from './components/LanguageSelector'
import { ValueEditorLanguage } from './types'

import './ValueEditor.scss'

export interface ValueEditorProps {
  className?: string
  'data-test'?: string
  disabled?: boolean
  // Renders the field's label and wires it to the editor. Callers used to
  // render their own, which is why three different label treatments grew up
  // around this component and none of them named the editor.
  label?: ReactNode
  // Sits beside the label, past the tooltip icon: a weight, a count, a
  // status. A sibling rather than label content, so it stays out of the
  // editor's accessible name.
  labelAfter?: ReactNode
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
  labelAfter,
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
  const [language, setLanguage] = useState<ValueEditorLanguage>(
    languageProp ?? 'txt',
  )
  const labelId = useId()
  const text = value === undefined || value === null ? '' : `${value}`

  // True once the format is decided: the caller pinned it, we detected JSON, or
  // someone picked one. Detection waits for a value rather than running on
  // mount, because values load after mount and a mount-only check left a JSON
  // value rendering as plaintext.
  const formatSettled = useRef(!!languageProp)

  useEffect(() => {
    if (formatSettled.current || !text) return
    formatSettled.current = true
    try {
      if (typeof JSON.parse(text) === 'object') {
        setLanguage('json')
      }
    } catch (e) {}
  }, [text])

  const pickLanguage = (next: ValueEditorLanguage) => {
    formatSettled.current = true
    setLanguage(next)
  }

  // The format row and copy are both editing affordances.
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
            <div className='value-editor__label'>
              <FieldLabel id={labelId} tooltip={labelTooltip}>
                {label}
              </FieldLabel>
              {labelAfter}
            </div>
          )}
          {showControls && (
            <LanguageSelector
              language={language}
              onChange={pickLanguage}
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
