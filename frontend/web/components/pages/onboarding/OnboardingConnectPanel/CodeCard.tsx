import React, { FC, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Highlight from 'components/Highlight'
import { useCopyFeedback } from 'components/pages/onboarding/hooks/useCopyFeedback'

export type CodeCardProps = {
  code: string
  // highlight.js language for the body.
  language: string
  headerLeft: ReactNode
  // Drives the verify checklist.
  onCopy?: () => void
  // Accessible name; the visible "Copy Code" label is identical on every card.
  copyLabel?: string
}

const CodeCard: FC<CodeCardProps> = ({
  code,
  copyLabel,
  headerLeft,
  language,
  onCopy,
}) => {
  const { copied, copy } = useCopyFeedback()

  return (
    <div className='onboarding-connect__codecard bg-surface-muted'>
      <div className='onboarding-connect__codecard-head d-flex align-items-center'>
        <div className='d-flex align-items-center gap-2'>{headerLeft}</div>
        <Button
          theme='primary'
          size='small'
          className='ms-auto'
          aria-label={copyLabel}
          onClick={() => {
            copy(code)
            onCopy?.()
          }}
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
      <Highlight embedded forceExpanded className={language}>
        {code}
      </Highlight>
    </div>
  )
}

export default CodeCard
