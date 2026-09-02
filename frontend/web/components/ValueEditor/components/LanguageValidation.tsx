import React, { FC, ReactNode } from 'react'

import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'

import {
  LANGUAGE_LABELS,
  ValueEditorLanguage,
} from 'components/ValueEditor/types'

interface LanguageValidationProps {
  language: ValueEditorLanguage
  // The parse error for the current value, or false when it is valid. Computed
  // by ValueEditor, so this stays presentational and can be rendered anywhere,
  // not only inside the format row.
  error: string | false
}

// Icon drops className for most icons and only a few spread their rest props,
// so the colour class goes on a wrapper and the icon inherits via currentColor.
const Wrapper: FC<{
  tone: 'success' | 'danger'
  children: ReactNode
  id?: string
}> = ({ children, id, tone }) => (
  <span id={id} className={`language-icon text-${tone}`}>
    {children}
  </span>
)

/** Tick or warning for the current value under the active format. */
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
        // saveFeatureWithValidation reads this id off the DOM to decide
        // whether to warn before saving. ValueEditor now reports validity
        // through onValidityChange; the id stays until that caller moves over.
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
