import React, { FC, ReactNode } from 'react'

import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'

import {
  LANGUAGE_LABELS,
  ValueEditorError,
  ValueEditorLanguage,
} from 'components/ValueEditor/types'

interface LanguageValidationProps {
  language: ValueEditorLanguage
  error: ValueEditorError
}

// Icon drops className for most icons, so the colour class goes on a wrapper
// and the icon inherits it via currentColor.
type ValidationTone = 'success' | 'danger'

const Wrapper: FC<{
  tone: ValidationTone
  children: ReactNode
  id?: string
}> = ({ children, id, tone }) => (
  <span id={id} className={`d-flex align-items-center text-${tone}`}>
    {children}
  </span>
)

const LanguageValidation: FC<LanguageValidationProps> = ({
  error,
  language,
}) => {
  if (!error) {
    return (
      <Wrapper tone='success'>
        <Icon name='checkmark-circle' width={14} />
      </Wrapper>
    )
  }

  const name = LANGUAGE_LABELS[language].replace('.', '')
  return (
    <Tooltip
      title={
        // saveFeatureWithValidation reads this id off the DOM to decide whether
        // to warn before saving, so it stays until that caller moves over.
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
