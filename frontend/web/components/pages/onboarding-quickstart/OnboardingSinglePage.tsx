import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import Utils from 'common/utils/utils'
import CodeSnippet from 'web/components/pages/onboarding-quickstart/components/CodeSnippet'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

type ConnectTab = 'ai' | 'manual'

type OnboardingSinglePageProps = {
  environmentKey: string
  featureName: string
  onGoToDashboard: () => void
  organisationName: string
  projectName: string
  // Becomes true when the SDK makes its first real request. Wired to the real
  // "first traffic" signal when it exists — never faked. Until then it stays
  // in the waiting state, which is honest.
  connected?: boolean
}

const OnboardingSinglePage: FC<OnboardingSinglePageProps> = ({
  connected = false,
  environmentKey,
  featureName,
  onGoToDashboard,
  organisationName,
  projectName,
}) => {
  const [tab, setTab] = useState<ConnectTab>('ai')
  const [flagOn, setFlagOn] = useState(true)
  const [copiedPrompt, setCopiedPrompt] = useState(false)

  // No-MCP path: the prompt carries the pre-created env key + flag, so the
  // user's coding agent can wire it in with zero extra setup.
  const aiPrompt = `Onboard me to Flagsmith. Environment key '${environmentKey}', flag '${featureName}'. Detect my stack, install the SDK, wire the flag in, run it, and verify it evaluates.`

  const copyPrompt = () => {
    Utils.copyToClipboard(aiPrompt)
    setCopiedPrompt(true)
    setTimeout(() => setCopiedPrompt(false), 1500)
  }

  return (
    <div className='onboarding-single'>
      <div className='onboarding-single__page'>
        <header className='onboarding-single__heading'>
          <div className='onboarding-single__crumb text-muted'>
            Onboarding / Connect your app
          </div>
          <h1 className='onboarding-single__title mb-0'>
            {connected
              ? 'You’re live — your first flag is working'
              : 'You’re set up — now connect your app'}
          </h1>
          <p className='onboarding-single__subtitle text-muted mb-0'>
            {connected
              ? `${featureName} is now evaluating in your app. Flip it and your app changes — no deploy.`
              : 'We created your project and a flag. Wire Flagsmith into your app — your AI agent can do it for you, or copy the snippet.'}
          </p>
        </header>

        {/* Pre-created resources — created at signup, shown for reassurance. */}
        <div className='onboarding-single__resources d-inline-flex align-items-center gap-2 rounded-md border border-default bg-surface-default'>
          <span className='text-muted'>Organisation</span>
          <span className='onboarding-single__chip rounded-sm bg-surface-subtle text-default'>
            {organisationName}
          </span>
          <span className='text-muted'>·</span>
          <span className='text-muted'>Project</span>
          <span className='onboarding-single__chip rounded-sm bg-surface-subtle text-default'>
            {projectName}
          </span>
          <span className='text-muted'>·</span>
          <span className='text-muted'>Flag</span>
          <span className='onboarding-single__chip onboarding-single__chip--flag rounded-sm text-action'>
            {featureName}
          </span>
        </div>

        <div className='onboarding-single__connect rounded-lg border border-default bg-surface-default'>
          <div className='onboarding-single__tabs d-flex align-items-center gap-4'>
            <button
              type='button'
              className={`onboarding-single__tab${
                tab === 'ai' ? ' onboarding-single__tab--active' : ''
              }`}
              onClick={() => setTab('ai')}
            >
              Connect with AI
            </button>
            <button
              type='button'
              className={`onboarding-single__tab${
                tab === 'manual' ? ' onboarding-single__tab--active' : ''
              }`}
              onClick={() => setTab('manual')}
            >
              Connect manually
            </button>
          </div>

          {tab === 'ai' ? (
            <div className='onboarding-single__panel d-flex flex-column gap-3'>
              <span className='text-default fw-semibold'>
                Paste this into your AI coding agent’s chat
              </span>
              <div className='onboarding-single__prompt d-flex align-items-start gap-3 rounded-md'>
                <code className='onboarding-single__prompt-text flex-fill'>
                  {aiPrompt}
                </code>
                <Button theme='outline' size='small' onClick={copyPrompt}>
                  <span className='d-inline-flex align-items-center gap-1'>
                    <Icon name='copy' width={14} />
                    {copiedPrompt ? 'Copied' : 'Copy'}
                  </span>
                </Button>
              </div>
              <div>
                <span className='text-default fw-semibold'>
                  What happens next
                </span>
                <ul className='onboarding-single__steps text-muted mt-2 mb-0'>
                  <li>
                    Detects your stack — language, framework, package manager.
                  </li>
                  <li>
                    Installs the Flagsmith SDK and wires it into your code.
                  </li>
                  <li>
                    Uses your flag {featureName} and verifies it’s working.
                  </li>
                </ul>
              </div>
            </div>
          ) : (
            <div className='onboarding-single__panel d-flex flex-column gap-3'>
              <span className='text-default fw-semibold'>
                Copy this into your app, then run it
              </span>
              <CodeSnippet
                environmentKey={environmentKey}
                featureName={featureName}
              />
            </div>
          )}
        </div>

        {/* Honest verify signal — waiting until a real request lands, never
            faked. Goes green only when `connected` is true. */}
        <div
          className={`onboarding-single__verify d-flex align-items-center gap-3 rounded-lg ${
            connected
              ? 'onboarding-single__verify--connected'
              : 'onboarding-single__verify--waiting'
          }`}
        >
          <span
            className={`onboarding-single__verify-dot ${
              connected
                ? 'onboarding-single__verify-dot--connected'
                : 'onboarding-single__verify-dot--waiting'
            }`}
            aria-hidden='true'
          />
          <div>
            <div className='onboarding-single__verify-title'>
              {connected
                ? '✓ First request received — you’re connected'
                : 'Waiting for your first request…'}
            </div>
            <div className='onboarding-single__verify-sub'>
              {connected
                ? 'Your app is reading flags from Flagsmith — flip the toggle and watch it change.'
                : 'However you connect, run your app and it lights up here — for real.'}
            </div>
          </div>
        </div>

        <div className='onboarding-single__flag d-flex align-items-center gap-2'>
          <span className='text-muted'>Your flag</span>
          <code className='text-action'>{featureName}</code>
          <div className='ms-auto d-flex align-items-center gap-2'>
            <span className='text-muted'>{flagOn ? 'On' : 'Off'}</span>
            <Switch
              checked={flagOn}
              onChange={() => setFlagOn((value) => !value)}
              aria-label={`Toggle ${featureName}`}
            />
          </div>
        </div>

        <div>
          <Button theme='text' onClick={onGoToDashboard}>
            Take me to the dashboard →
          </Button>
        </div>
      </div>
    </div>
  )
}

OnboardingSinglePage.displayName = 'OnboardingSinglePage'

export default OnboardingSinglePage
