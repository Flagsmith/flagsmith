import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import GhostInput from 'components/base/forms/GhostInput'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import CodeSnippet from 'web/components/pages/onboarding-quickstart/components/CodeSnippet'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

type ConnectTab = 'ai' | 'manual'

type OnboardingSinglePageProps = {
  environmentKey: string
  featureName: string
  // The flag's real `enabled` state in the Development environment, and a
  // handler that persists a toggle to Flagsmith. Not local UI state — flipping
  // this actually changes the flag, which is the whole point of the page.
  flagEnabled: boolean
  flagToggleDisabled?: boolean
  onToggleFlag: () => void
  onGoToDashboard: () => void
  onRenameOrganisation?: (name: string) => void
  onRenameProject?: (name: string) => void
  organisationName: string
  projectName: string
  // Becomes true when the SDK makes its first real request. Wired to the real
  // "first traffic" signal when it exists — never faked. Until then it stays
  // in the waiting state, which is honest.
  connected?: boolean
}

type EditableChipProps = {
  label: string
  onCommit: (next: string) => void
  value: string
}

// An inline-editable chip built on the shared GhostInput (the transparent,
// auto-sizing text field used for inline renames elsewhere). Keeps a local
// draft and commits on blur / Enter; an empty value reverts to the last good
// name rather than persisting a blank.
const EditableChip: FC<EditableChipProps> = ({ label, onCommit, value }) => {
  const [draft, setDraft] = useState(value)

  const commit = () => {
    const next = draft.trim()
    if (!next) {
      setDraft(value)
      return
    }
    if (next !== value) {
      onCommit(next)
    }
  }

  return (
    <span className='onboarding-single__chip onboarding-single__chip--editable d-inline-flex align-items-center gap-1 rounded-sm bg-surface-subtle text-default'>
      <GhostInput
        value={draft}
        placeholder={label}
        aria-label={`${label} name`}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.currentTarget.blur()
          }
        }}
      />
      <Icon
        name='edit'
        width={12}
        fill='var(--color-icon-secondary)'
        aria-hidden
      />
    </span>
  )
}

const OnboardingSinglePage: FC<OnboardingSinglePageProps> = ({
  connected = false,
  environmentKey,
  featureName,
  flagEnabled,
  flagToggleDisabled = false,
  onGoToDashboard,
  onRenameOrganisation,
  onRenameProject,
  onToggleFlag,
  organisationName,
  projectName,
}) => {
  const [tab, setTab] = useState<ConnectTab>('ai')
  const [copiedPrompt, setCopiedPrompt] = useState(false)

  // No-MCP path: the prompt carries the pre-created env key + flag, so the
  // user's coding agent can wire it in with zero extra setup. When this app
  // isn't on the default SaaS endpoint (staging / self-hosted / region), the
  // SDK would otherwise default to edge.api.flagsmith.com and silently fail to
  // authenticate — so we inject the real API base URL the key belongs to and
  // tell the agent to wire it into the SDK's api/apiUrl option, not just the
  // test. The honesty instruction mirrors the "demonstrate, don't simulate"
  // principle: the agent must observe a real evaluation before claiming success.
  const apiBaseUrl = Constants.getFlagsmithSDKUrl()
  const apiLine = Constants.isCustomFlagsmithUrl()
    ? `\n- API base URL: ${apiBaseUrl} (set the SDK's api/apiUrl option to this — not just for the test)`
    : ''
  const aiPrompt = `Onboard me to Flagsmith.
- Environment key: ${environmentKey}
- Flag: ${featureName}${apiLine}
Detect my stack, install the matching SDK, and wire the flag into one representative spot (keep the diff small). Then run the app so the SDK actually evaluates '${featureName}', and only tell me it works if you genuinely observed the evaluation — don't fabricate the result. If the key doesn't authenticate, it's almost always the API base URL (staging/self-hosted), not a bad key — don't loop over keys.`

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
          <EditableChip
            label='Organisation'
            value={organisationName}
            onCommit={(name) => onRenameOrganisation?.(name)}
          />
          <span className='text-muted'>·</span>
          <span className='text-muted'>Project</span>
          <EditableChip
            label='Project'
            value={projectName}
            onCommit={(name) => onRenameProject?.(name)}
          />
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
            <span className='text-muted'>{flagEnabled ? 'On' : 'Off'}</span>
            <Switch
              checked={flagEnabled}
              disabled={flagToggleDisabled}
              onChange={onToggleFlag}
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
