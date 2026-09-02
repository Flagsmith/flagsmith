import React, { FC, MouseEvent } from 'react'
import cx from 'classnames'

import {
  LANGUAGES,
  LANGUAGE_LABELS,
  ValueEditorLanguage,
} from 'components/ValueEditor/types'
import LanguageValidation from './LanguageValidation'

interface LanguageSelectorProps {
  language: ValueEditorLanguage
  onChange: (language: ValueEditorLanguage) => void
  value: string
}

/** The .txt/.json/.xml/.toml/.yaml row above the editor. */
const LanguageSelector: FC<LanguageSelectorProps> = ({
  language,
  onChange,
  value,
}) => (
  <Row className='select-language gap-1'>
    {LANGUAGES.map((option) => (
      <span
        key={option}
        // mousedown, not click: the editor is contenteditable and a click
        // would blur it before the language change lands.
        onMouseDown={(e: MouseEvent) => {
          e.preventDefault()
          e.stopPropagation()
          onChange(option)
        }}
        className={cx(option, { active: language === option })}
      >
        {LANGUAGE_LABELS[option]}{' '}
        {option !== 'txt' && language === option && (
          <LanguageValidation language={option} value={value} />
        )}
      </span>
    ))}
  </Row>
)

export default LanguageSelector
