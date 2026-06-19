import React, { FC, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Highlight from 'components/Highlight'
import { useCopyFeedback } from 'components/pages/onboarding/hooks/useCopyFeedback'

export type CodeCardProps = {
  code: string
  // Syntax language for the body's highlighting (e.g. 'bash', 'javascript').
  language: string
  // Left side of the card header (e.g. the language label or npm/yarn pills).
  headerLeft: ReactNode
}

// Owns its own "Copied" feedback so each card is independent. Highlight escapes
// the body for display; Copy uses the raw string.
const CodeCard: FC<CodeCardProps> = ({ code, headerLeft, language }) => {
  const { copied, copy } = useCopyFeedback()

  return (
    <div className='onboarding-connect__codecard bg-surface-muted'>
      <div className='onboarding-connect__codecard-head d-flex align-items-center'>
        <div className='d-flex align-items-center gap-2'>{headerLeft}</div>
        <Button
          theme='primary'
          size='small'
          className='ms-auto'
          onClick={() => copy(code)}
        >
          <span
            className='d-inline-flex align-items-center gap-1'
            aria-live='polite'
          >
            <Icon name='copy' width={14} />
            {copied ? 'Copied' : 'Copy Code'}
          </span>
        </Button>
      </div>
      <Highlight forceExpanded className={language}>
        {code}
      </Highlight>
    </div>
  )
}

export default CodeCard
