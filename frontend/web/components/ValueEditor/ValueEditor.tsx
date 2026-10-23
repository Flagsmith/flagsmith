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
import { ValueEditorLanguage } from './types'
import { validateValue } from './validate'

import './ValueEditor.scss'

export interface ValueEditorProps {
  className?: string
  disabled?: boolean
  // Required: it is what names the editor. Rendered as a FieldLabel wired to
  // it, so callers cannot get the association wrong.
  label: ReactNode
  // Sits beside the label, outside it, so it stays out of the editor's
  // accessible name.
  labelAfter?: ReactNode
  labelTooltip?: string
  language?: ValueEditorLanguage
  onBlur?: () => void
  // A string, not FlagsmithValue: deciding that "123" is a number is the
  // caller's job (Utils.getTypedValue, Utils.valueToFeatureState).
  onChange?: (value: string) => void
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
  value,
}) => {
  const [picked, setPicked] = useState<ValueEditorLanguage>()
  const [detected, setDetected] = useState<ValueEditorLanguage>()
  // Derived, not state: a caller that changes `language` has to win on the
  // next render, and useState would keep whatever it read on mount.
  const language = languageProp ?? picked ?? detected ?? 'txt'
  const labelId = useId()
  const text = value === undefined || value === null ? '' : `${value}`

  // Detection waits for a value rather than running on mount: values load
  // after mount, and a mount-only check left JSON rendering as plaintext.
  const detectionDone = useRef(false)

  useEffect(() => {
    if (languageProp || picked || detectionDone.current || !text) return
    detectionDone.current = true
    try {
      if (typeof JSON.parse(text) === 'object') {
        setDetected('json')
      }
    } catch (e) {}
  }, [text, languageProp, picked])

  const pickLanguage = (next: ValueEditorLanguage) => setPicked(next)

  // A caller that pins the format has nothing to switch, so the row goes, and
  // copy goes with it as it always has.
  const showControls = !disabled && !languageProp

  // Only rendered alongside the format row, so a pinned caller does not need a
  // DOMParser run on every keystroke.
  const error = useMemo(
    () => (showControls ? validateValue(language, text) : false),
    [language, text, showControls],
  )

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
