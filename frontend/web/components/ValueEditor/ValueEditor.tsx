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
  onBlur?: () => void
  // The edited text. Deliberately a string, not FlagsmithValue: this edits
  // text, and deciding that "123" is a number is Flagsmith's domain logic.
  // Callers interpret it (Utils.getTypedValue, Utils.valueToFeatureState).
  onChange?: (value: string) => void
  // Fires when the value stops or starts parsing under the active format.
  onValidityChange?: (error: string | false) => void
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

  // Validity lives here rather than in the format row, so it can be reported
  // to callers and rendered anywhere. Keeping it in the row is what left the
  // SAML field with language='xml' and no XML validation at all.
  const error = useMemo(() => validateValue(language, text), [language, text])

  useEffect(() => {
    onValidityChange?.(error)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error])

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
              error={error}
              language={language}
              onChange={pickLanguage}
            />
          )}
        </div>
      )}

      <div className='value-editor__field'>
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
