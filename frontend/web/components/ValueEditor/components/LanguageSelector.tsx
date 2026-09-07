import React, { FC, MouseEvent } from 'react'
import cx from 'classnames'

import BareButton from 'components/base/forms/BareButton'
import Row from 'components/base/grid/Row'

import {
  LANGUAGES,
  LANGUAGE_LABELS,
  ValueEditorLanguage,
} from 'components/ValueEditor/types'
import LanguageValidation from './LanguageValidation'

interface LanguageSelectorProps {
  language: ValueEditorLanguage
  onChange: (language: ValueEditorLanguage) => void
  error: string | false
}

/** The .txt/.json/.xml/.toml/.yaml row above the editor. */
const LanguageSelector: FC<LanguageSelectorProps> = ({
  error,
  language,
  onChange,
}) => (
  <Row
    className='select-language gap-1 ms-auto'
    role='group'
    aria-label='Value format'
  >
    {LANGUAGES.map((option) => (
      <BareButton
        key={option}
        // The editor is contenteditable: pressing down on a button would blur
        // it. preventDefault keeps the caret; the click still fires.
        onMouseDown={(e: MouseEvent) => e.preventDefault()}
        onClick={() => onChange(option)}
        aria-pressed={language === option}
        className={cx(option, 'd-flex align-items-center text-secondary', {
          active: language === option,
        })}
      >
        {LANGUAGE_LABELS[option]}{' '}
        {option !== 'txt' && language === option && (
          <LanguageValidation language={option} error={error} />
        )}
      </BareButton>
    ))}
  </Row>
)

export default LanguageSelector
