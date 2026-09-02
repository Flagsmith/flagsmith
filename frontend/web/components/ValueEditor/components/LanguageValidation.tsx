import React, { FC, useMemo } from 'react'

import Icon from 'components/icons/Icon'

import {
  LANGUAGE_LABELS,
  ValueEditorLanguage,
} from 'components/ValueEditor/types'
import { validateValue } from 'components/ValueEditor/validate'

interface LanguageValidationProps {
  language: ValueEditorLanguage
  value: string
}

// Icon drops className for most icons and only a few spread their rest props,
// so the colour class goes on a wrapper and the icon inherits via currentColor.
const Wrapper: FC<{
  tone: 'success' | 'danger'
  children: React.ReactNode
  id?: string
}> = ({ children, id, tone }) => (
  <span id={id} className={`language-icon text-${tone}`}>
    {children}
  </span>
)

/** Tick or warning beside the active format label. */
const LanguageValidation: FC<LanguageValidationProps> = ({
  language,
  value,
}) => {
  const error = useMemo(() => validateValue(language, value), [language, value])
  const name = LANGUAGE_LABELS[language].replace('.', '')

  if (!error) {
    return (
      <Wrapper tone='success'>
        <Icon name='checkmark-circle' width={14} />
      </Wrapper>
    )
  }

  return (
    <Tooltip
      title={
        // saveFeatureWithValidation reads this id off the DOM to decide
        // whether to warn before saving, so it has to stay.
        <Wrapper tone='danger' id='language-validation-error'>
          <Icon name='warning' width={14} fill='currentColor' />
        </Wrapper>
      }
    >
      {`${name} validation error, please check your value.<br/>Error: ${error}`}
    </Tooltip>
  )
}

export default LanguageValidation
