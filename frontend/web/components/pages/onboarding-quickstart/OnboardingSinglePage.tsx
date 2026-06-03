import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import GhostInput from 'components/base/forms/GhostInput'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import Highlight from 'components/Highlight'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

type ConnectTab = 'ai' | 'manual'
type ManualLang = 'React' | 'JavaScript'
const MANUAL_LANGS: ManualLang[] = ['React', 'JavaScript']

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
  const [manualLang, setManualLang] = useState<ManualLang>('React')
  const [copiedManual, setCopiedManual] = useState<string | null>(null)

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
    ? `\n- API base URL: ${apiBaseUrl} (use as the SDK's api/apiUrl)`
    : ''
  const aiPrompt = `Set up Flagsmith in this project.
- Environment key: ${environmentKey}
- Flag: ${featureName}${apiLine}
Detect my stack, install the SDK, and wire ${featureName} into one place. Then run the app and confirm ${featureName} actually evaluates before telling me it worked.`

  const copyPrompt = () => {
    Utils.copyToClipboard(aiPrompt)
    setCopiedPrompt(true)
    setTimeout(() => setCopiedPrompt(false), 1500)
  }

  const copyManual = (id: string, code: string) => {
    Utils.copyToClipboard(code)
    setCopiedManual(id)
    setTimeout(() => setCopiedManual(null), 1500)
  }

  // Render a code block for the manual path. Highlight escapes the content for
  // display (so JSX like <FlagsmithProvider> shows as text and highlights
  // instead of being parsed as HTML), while Copy uses the raw string — which is
  // why CodeHelp (innerHTML, escaping off) can't be used for JSX here.
  const renderManualCode = (id: string, code: string) => (
    <div>
      <div className='d-flex justify-content-end mb-1'>
        <Button
          theme='outline'
          size='small'
          onClick={() => copyManual(id, code)}
        >
          <span className='d-inline-flex align-items-center gap-1'>
            <Icon name='copy' width={14} />
            {copiedManual === id ? 'Copied' : 'Copy'}
          </span>
        </Button>
      </div>
      <Highlight forceExpanded className='javascript'>
        {code}
      </Highlight>
    </div>
  )

  // Purpose-built JS/React example for the manual path: it doesn't just check
  // the flag, it shows the actual payoff — gating a demo button on the real
  // flag. Concrete beats the maintained snippet's abstract placeholder. The API
  // URL is injected only when the app isn't on the default SaaS endpoint
  // (staging / self-hosted), matching the SDK's `api` option.
  const installSnippet =
    '// npm\nnpm i @flagsmith/flagsmith --save\n\n// yarn\nyarn add @flagsmith/flagsmith'

  const reactApiLine = Constants.isCustomFlagsmithUrl()
    ? `\n        api: '${apiBaseUrl}',`
    : ''
  const jsApiLine = Constants.isCustomFlagsmithUrl()
    ? `\n  api: '${apiBaseUrl}',`
    : ''
  const wireSnippets = {
    JavaScript: `import flagsmith from '@flagsmith/flagsmith'

// Initialise the SDK
await flagsmith.init({
  environmentID: '${environmentKey}',${jsApiLine}
})

// Show the demo button only when your flag is on
const demoButton = document.querySelector('#demo-button')
if (flagsmith.hasFeature('${featureName}')) {
  demoButton.hidden = false
}`,
    React: `import flagsmith from '@flagsmith/flagsmith'
import { FlagsmithProvider, useFlags } from '@flagsmith/flagsmith/react'

// Wrap your app once, at the root
function App() {
  return (
    <FlagsmithProvider
      flagsmith={flagsmith}
      options={{
        environmentID: '${environmentKey}',${reactApiLine}
      }}
    >
      <YourApp />
    </FlagsmithProvider>
  )
}

// Then gate the demo button on your flag
function Header() {
  const { ${featureName} } = useFlags(['${featureName}'])
  return <nav>{${featureName}.enabled && <button>Demo</button>}</nav>
}`,
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
        <div className='onboarding-single__resources d-inline-flex flex-wrap align-items-center gap-2 rounded-md border border-default bg-surface-default'>
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
            <div className='onboarding-single__panel d-flex flex-column gap-4'>
              <div className='onboarding-single__sdks d-flex gap-2'>
                {MANUAL_LANGS.map((lang) => (
                  <button
                    key={lang}
                    type='button'
                    className={`onboarding-single__sdk${
                      manualLang === lang
                        ? ' onboarding-single__sdk--active'
                        : ''
                    }`}
                    onClick={() => setManualLang(lang)}
                  >
                    {lang}
                  </button>
                ))}
              </div>
              <div>
                <div className='onboarding-single__step-title text-default fw-semibold mb-2'>
                  1. Install the SDK
                </div>
                {renderManualCode('install', installSnippet)}
              </div>
              <div>
                <div className='onboarding-single__step-title text-default fw-semibold mb-2'>
                  2. Wire it in &amp; gate your demo button
                </div>
                {renderManualCode('wire', wireSnippets[manualLang])}
              </div>
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
