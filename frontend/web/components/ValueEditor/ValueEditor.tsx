import React, {
  FC,
  ReactNode,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from 'react'
import cx from 'classnames'

import FieldLabel from 'components/base/forms/FieldLabel'
import Highlight from 'components/Highlight'
import { FlagsmithValue } from 'common/types/responses'

import CopyValueButton from './components/CopyValueButton'
import LanguageSelector from './components/LanguageSelector'
import { ValueEditorError, ValueEditorLanguage } from './types'
import { validateValue } from './validate'

import './ValueEditor.scss'

export interface ValueEditorProps {
  className?: string
  'data-test'?: string
  disabled?: boolean
  // Rendered as a FieldLabel wired to the editor, so callers cannot get the
  // association wrong.
  label?: ReactNode
  // Sits beside the label, outside it, so it stays out of the editor's
  // accessible name.
  labelAfter?: ReactNode
  labelTooltip?: string
  language?: ValueEditorLanguage
  onBlur?: () => void
  // A string, not FlagsmithValue: deciding that "123" is a number is the
  // caller's job (Utils.getTypedValue, Utils.valueToFeatureState).
  onChange?: (value: string) => void
  // Fires when the value stops or starts parsing under the active format.
  onValidityChange?: (error: ValueEditorError) => void
  value?: FlagsmithValue
}

const ValueEditor: FC<ValueEditorProps> = ({
  className,
  disabled,
  label,
  labelAfter,
  labelTooltip,
  language: languageProp,
  onBlur,
  onChange,
  onValidityChange,
  value,
  ...rest
}) => {
  const [language, setLanguage] = useState<ValueEditorLanguage>(
    languageProp ?? 'txt',
  )
  const labelId = useId()
  const text = value === undefined || value === null ? '' : `${value}`

  // Detection waits for a value rather than running on mount: values load
  // after mount, and a mount-only check left JSON rendering as plaintext.
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

  const error = useMemo(() => validateValue(language, text), [language, text])

  useEffect(() => {
    onValidityChange?.(error)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error])

  const pickLanguage = (next: ValueEditorLanguage) => {
    formatSettled.current = true
    setLanguage(next)
  }

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
        <div className='value-editor__header d-flex align-items-center justify-content-between gap-2 mb-1'>
          {label && (
            <div className='d-flex align-items-center gap-2'>
              <FieldLabel className='mb-0' id={labelId} tooltip={labelTooltip}>
                {label}
              </FieldLabel>
              {labelAfter}
            </div>
          )}
          {showControls && (
            <LanguageSelector
              error={error}
              language={language}
              onChange={pickLanguage}
            />
          )}
        </div>
      )}

      <div className='value-editor__field position-relative'>
        {showControls && <CopyValueButton value={text} />}

        <Highlight
          aria-labelledby={label ? labelId : undefined}
          aria-readonly={disabled || undefined}
          data-test={rest['data-test']}
          disabled={disabled}
          onChange={disabled ? null : onChange}
          onBlur={disabled ? null : onBlur}
          role='textbox'
          className={language}
        >
          {text}
        </Highlight>
      </div>
    </div>
  )
}

export default ValueEditor
