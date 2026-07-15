import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Constants from 'common/constants'
import { useCopyFeedback } from 'components/pages/onboarding/hooks/useCopyFeedback'

export type ConnectWithAiPanelProps = {
  environmentKey: string
  featureName: string
}

// "Connect with AI" tab: an agent-agnostic prompt the user pastes into their
// coding agent. The prompt carries the pre-created env key + flag so an agent
// can wire it in with zero setup. Off the default SaaS endpoint we inject the
// real API base URL (the SDK would otherwise default to edge and silently fail
// to auth), and tell the agent to confirm a real evaluation before claiming
// success.
const ConnectWithAiPanel: FC<ConnectWithAiPanelProps> = ({
  environmentKey,
  featureName,
}) => {
  const { copied, copy } = useCopyFeedback()

  const apiBaseUrl = Constants.getFlagsmithSDKUrl()
  const apiLine = Constants.isCustomFlagsmithUrl()
    ? `\n- API base URL: ${apiBaseUrl} (use as the SDK's api/apiUrl)`
    : ''
  const aiPrompt = `Set up Flagsmith in this project.
- Environment key: ${environmentKey}
- Flag: ${featureName}${apiLine}
Detect my stack, install the SDK, and wire ${featureName} into one place. Then run the app and confirm ${featureName} actually evaluates before telling me it worked.`

  return (
    <>
      <span className='text-default font-weight-semibold'>
        Paste this into your AI coding agent’s chat
      </span>
      <div className='bg-surface-muted p-3 d-flex align-items-start gap-3 rounded-md'>
        <code className='onboarding-connect__prompt-text flex-fill'>
          {aiPrompt}
        </code>
        <Button theme='outline' size='small' onClick={() => copy(aiPrompt)}>
          <span
            className='d-inline-flex align-items-center gap-1'
            aria-live='polite'
          >
            <Icon name='copy' width={14} />
            {copied ? 'Copied' : 'Copy'}
          </span>
        </Button>
      </div>
      <div>
        <span className='text-default font-weight-semibold'>
          What happens next
        </span>
        <ul className='onboarding-connect__steps text-muted mt-2 mb-0'>
          <li>Detects your stack: language, framework and package manager.</li>
          <li>Installs the Flagsmith SDK and wires it into your code.</li>
          <li>Uses your flag {featureName} and verifies it’s working.</li>
        </ul>
      </div>
    </>
  )
}

export default ConnectWithAiPanel
