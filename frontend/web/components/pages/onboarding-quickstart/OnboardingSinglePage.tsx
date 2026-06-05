import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import GhostInput from 'components/base/forms/GhostInput'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import Highlight from 'components/Highlight'
import {
  getManualSnippets,
  ManualLang,
  MANUAL_LANGS,
} from 'web/components/pages/onboarding-quickstart/manualSnippets'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

type ConnectTab = 'ai' | 'manual'

type Quest = { desc: string; key: string; title: string }

// "What's your next quest" cards — illustrative for now (the flows behind each
// are future work, per the design review). Shown grayed until first traffic.
const QUESTS: Quest[] = [
  {
    desc: 'Turn a feature off instantly — no deploy.',
    key: 'kill',
    title: 'Kill switch',
  },
  {
    desc: 'Ship to a % of your users.',
    key: 'rollout',
    title: 'Gradual rollout',
  },
  {
    desc: 'A/B test which variant wins.',
    key: 'experiment',
    title: 'Experiment',
  },
  {
    desc: 'Serve a value, not just on/off.',
    key: 'config',
    title: 'Remote config',
  },
]

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
  const [tab, setTab] = useState<ConnectTab>('manual')
  const [copiedPrompt, setCopiedPrompt] = useState(false)
  const [manualLang, setManualLang] = useState<ManualLang>('React')
  const [copiedManual, setCopiedManual] = useState<string | null>(null)
  const [installPm, setInstallPm] = useState<'npm' | 'yarn'>('npm')
  const [copiedInstall, setCopiedInstall] = useState(false)
  const [copiedCode, setCopiedCode] = useState(false)

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
    // Tick the matching checklist item (stays ticked).
    if (id === 'install') {
      setCopiedInstall(true)
    } else {
      setCopiedCode(true)
    }
    setTimeout(() => setCopiedManual(null), 1500)
  }

  // Render a code card for the manual path: a header bar (left slot for
  // pills/language, a Copy Code button on the right) over the code body.
  // Highlight escapes the content for display (so JSX shows as text and
  // highlights instead of being parsed as HTML), while Copy uses the raw string
  // — which is why CodeHelp (innerHTML, escaping off) can't be used here.
  const renderManualCode = (
    id: string,
    code: string,
    hljsClass: string,
    headerLeft: React.ReactNode,
  ) => (
    <div className='onboarding-single__codecard'>
      <div className='onboarding-single__codecard-head d-flex align-items-center'>
        <div className='d-flex align-items-center gap-2'>{headerLeft}</div>
        <Button
          theme='primary'
          size='small'
          className='ms-auto'
          onClick={() => copyManual(id, code)}
        >
          <span className='d-inline-flex align-items-center gap-1'>
            <Icon name='copy' width={14} fill='white' />
            {copiedManual === id ? 'Copied' : 'Copy Code'}
          </span>
        </Button>
      </div>
      <Highlight forceExpanded className={hljsClass}>
        {code}
      </Highlight>
    </div>
  )

  // One console checklist line: [✓]/[ ] + label, green when done, dim when not.
  const renderCheck = (done: boolean, label: string, doneClass = 'ok') => (
    <code
      className={`onboarding-single__console-line onboarding-single__console-line--${
        done ? doneClass : 'pending'
      }`}
    >
      {`${done ? '[✓]' : '[ ]'} ${label}`}
    </code>
  )

  // Per-language manual snippets (install + wire), matching the design. API URL
  // injected only off the default SaaS endpoint. See manualSnippets.ts.
  const manualSnippets = getManualSnippets({
    apiUrl: apiBaseUrl,
    environmentKey,
    featureName,
    isCustomUrl: Constants.isCustomFlagsmithUrl(),
  })
  const manualSnip = manualSnippets[manualLang]
  const installCode =
    manualSnip.installYarn && installPm === 'yarn'
      ? manualSnip.installYarn
      : manualSnip.install

  // Radar column: a bold status title + a detail subtitle. Copy progress lives
  // in the checklist, not here.
  const verifyTitle = connected ? 'Signal received!' : 'Waiting for the signal'
  const verifyHeadline = connected
    ? `${featureName} just evaluated for the first time.`
    : `Run your app — ${featureName} lights up here.`

  // Illustrative visual for each "next quest" card.
  const questVisual = (key: string) => {
    switch (key) {
      case 'kill':
        return <Switch checked disabled aria-label='Kill switch example' />
      case 'rollout':
        return (
          <div>
            <div className='onboarding-single__quest-bar'>
              <span className='onboarding-single__quest-bar-fill' />
            </div>
            <div className='onboarding-single__quest-bar-label text-muted mt-1'>
              25% of users
            </div>
          </div>
        )
      case 'experiment':
        return (
          <div className='onboarding-single__quest-ab'>
            <span className='onboarding-single__quest-ab-opt onboarding-single__quest-ab-opt--active'>
              A
            </span>
            <span className='onboarding-single__quest-ab-opt'>B</span>
          </div>
        )
      case 'config':
        return (
          <code className='onboarding-single__quest-config'>
            "theme": "dark"
          </code>
        )
      default:
        return null
    }
  }

  return (
    <div className='onboarding-single'>
      <div className='onboarding-single__page'>
        <header className='onboarding-single__heading'>
          <div className='onboarding-single__crumb text-muted'>
            Onboarding / Connect your app
          </div>
          <h1 className='onboarding-single__title mb-0'>
            Welcome — let’s get you live 👋
          </h1>
          {/* Pre-created resources, inline in the sentence; org/project editable. */}
          <p className='onboarding-single__subtitle text-muted mb-0'>
            We created your organisation{' '}
            <EditableChip
              label='Organisation'
              value={organisationName}
              onCommit={(name) => onRenameOrganisation?.(name)}
            />
            , your project{' '}
            <EditableChip
              label='Project'
              value={projectName}
              onCommit={(name) => onRenameProject?.(name)}
            />{' '}
            and your flag{' '}
            <span className='onboarding-single__chip onboarding-single__chip--flag rounded-sm text-action'>
              {featureName}
            </span>
          </p>
        </header>

        <div className='onboarding-single__connect rounded-lg border border-default bg-surface-default'>
          <div className='onboarding-single__connect-head d-flex align-items-center justify-content-between'>
            <button
              type='button'
              className={`onboarding-single__connect-tab${
                tab === 'manual'
                  ? ' onboarding-single__connect-tab--active'
                  : ''
              }`}
              onClick={() => setTab('manual')}
            >
              Connect your code
            </button>
            <button
              type='button'
              className={`onboarding-single__connect-ai${
                tab === 'ai' ? ' onboarding-single__connect-ai--active' : ''
              }`}
              onClick={() => setTab('ai')}
            >
              <span className='onboarding-single__sparkle' aria-hidden>
                ✦
              </span>
              Connect with AI
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
              <div className='onboarding-single__sdks d-flex flex-wrap gap-2'>
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
                <div className='onboarding-single__step-head d-flex align-items-center gap-2 mb-2'>
                  <span className='onboarding-single__step-num'>1</span>
                  <span className='onboarding-single__step-title text-default fw-semibold'>
                    Install the SDK
                  </span>
                </div>
                {renderManualCode(
                  'install',
                  installCode,
                  'bash',
                  manualSnip.installYarn ? (
                    <div className='onboarding-single__pm d-inline-flex'>
                      {(['npm', 'yarn'] as const).map((pm) => (
                        <button
                          key={pm}
                          type='button'
                          className={`onboarding-single__pm-opt${
                            installPm === pm
                              ? ' onboarding-single__pm-opt--active'
                              : ''
                          }`}
                          onClick={() => setInstallPm(pm)}
                        >
                          {pm}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <span className='onboarding-single__codecard-lang'>
                      {manualLang}
                    </span>
                  ),
                )}
              </div>
              <div>
                <div className='onboarding-single__step-head d-flex align-items-center gap-2 mb-2'>
                  <span className='onboarding-single__step-num'>2</span>
                  <span className='onboarding-single__step-title text-default fw-semibold'>
                    Wire it in &amp; take instant control of what users see
                  </span>
                </div>
                {renderManualCode(
                  'wire',
                  manualSnip.wire,
                  manualSnip.hljs,
                  <span className='onboarding-single__codecard-lang'>
                    {manualLang}
                  </span>,
                )}
              </div>
            </div>
          )}
        </div>

        {/* Verify (v3) — two columns: a sonar (left) and a live SDK console
            with the flag card beneath it (right). Honest: the console only
            shows a successful evaluation once `connected` is true; until then
            it sits in the listening/scanning state. */}
        <div
          className={`onboarding-single__verify rounded-lg border border-default onboarding-single__verify--${
            connected ? 'connected' : 'waiting'
          }`}
        >
          <div className='onboarding-single__verify-left'>
            <div className='onboarding-single__verify-badges d-flex align-items-center justify-content-between'>
              <span className='onboarding-single__badge'>
                <span className='onboarding-single__badge-dot' aria-hidden />
                {connected ? 'Evaluation received' : 'Signal detection active'}
              </span>
              <span className='onboarding-single__badge'>
                <span className='onboarding-single__badge-dot' aria-hidden />
                {connected ? 'First ping detected' : 'Scanning for ping'}
              </span>
            </div>
            <div className='onboarding-single__radar' aria-hidden>
              <span className='onboarding-single__radar-ring onboarding-single__radar-ring--4' />
              <span className='onboarding-single__radar-ring onboarding-single__radar-ring--3' />
              <span className='onboarding-single__radar-ring onboarding-single__radar-ring--2' />
              <span className='onboarding-single__radar-ring onboarding-single__radar-ring--1' />
              <span className='onboarding-single__radar-dot' />
            </div>
            <div className='onboarding-single__verify-title text-center'>
              {verifyTitle}
            </div>
            <div className='onboarding-single__verify-line text-center'>
              {verifyHeadline}
            </div>
          </div>

          <div className='onboarding-single__verify-right'>
            {/* SDK console, but its body is the honest checklist — every line
                ticks on a real event (pre-created, the Copy click, a real
                request). Keeps the terminal look without faking SDK output. */}
            <div className='onboarding-single__console'>
              <div className='onboarding-single__console-head'>
                <span className='onboarding-single__console-light onboarding-single__console-light--r' />
                <span className='onboarding-single__console-light onboarding-single__console-light--y' />
                <span className='onboarding-single__console-light onboarding-single__console-light--g' />
                <span className='onboarding-single__console-name'>
                  flagsmith — sdk console
                </span>
                <span className='onboarding-single__console-badge'>
                  ● {connected ? 'LIVE' : 'LISTENING'}
                </span>
              </div>
              <div className='onboarding-single__console-body'>
                {/* One checklist across both states. Copy items reflect real
                    Copy clicks; SDK/flags/evaluation tick on a real request.
                    Connected appends the request proof; waiting, the watch line. */}
                {renderCheck(copiedInstall, 'Install command copied')}
                {renderCheck(copiedCode, 'Code copied')}
                {renderCheck(connected, 'SDK initialized')}
                {renderCheck(
                  connected,
                  connected
                    ? `Flags loaded · ${featureName}: ${flagEnabled}`
                    : 'Flags loaded',
                )}
                {renderCheck(connected, 'First evaluation received', 'done')}
                {connected ? (
                  <>
                    {/* Real request metadata — illustrative values until wired
                        to the live first-request signal. */}
                    <code className='onboarding-single__console-line onboarding-single__console-line--meta'>
                      User-Agent: Chrome/120.0 · MacBook Pro
                    </code>
                    <code className='onboarding-single__console-line onboarding-single__console-line--meta'>
                      IP: 192.168.1.42 · 2024-01-15 14:23:01
                    </code>
                    <code className='onboarding-single__console-line onboarding-single__console-line--connected'>
                      ✓ Connected
                    </code>
                    {/* Toggle's now unlocked — nudge to flip it; reflects the
                        real flag state. */}
                    <code className='onboarding-single__console-line onboarding-single__console-line--prompt'>
                      {flagEnabled
                        ? `✓ ${featureName} is live`
                        : `→ flip ${featureName} on to see it change`}
                    </code>
                  </>
                ) : (
                  <>
                    <code className='onboarding-single__console-line onboarding-single__console-line--prompt'>
                      {`$ run your app — watching for ${featureName}'s first evaluation…`}
                    </code>
                    <code className='onboarding-single__console-line onboarding-single__console-line--cursor'>
                      ▋
                    </code>
                  </>
                )}
              </div>
            </div>

            {/* Flag toggle — gated until connected. Becomes the real,
                persisting control once a first request lands. */}
            <div
              className={`onboarding-single__flagcard rounded-md border border-default${
                connected ? '' : ' onboarding-single__flagcard--locked'
              }`}
            >
              <div className='onboarding-single__flagcard-head d-flex align-items-center gap-1'>
                {!connected && (
                  <Icon
                    name='lock'
                    width={14}
                    fill='var(--color-icon-secondary)'
                  />
                )}
                <span className='text-muted'>Your flag</span>
              </div>
              <div className='d-flex align-items-center gap-2'>
                <code className='onboarding-single__chip rounded-sm bg-surface-subtle text-default'>
                  {featureName}
                </code>
                <div className='ms-auto d-flex align-items-center gap-2'>
                  <span className='text-muted'>
                    {connected && flagEnabled ? 'On' : 'Off'}
                  </span>
                  <Switch
                    checked={connected && flagEnabled}
                    disabled={!connected || flagToggleDisabled}
                    onChange={onToggleFlag}
                    aria-label={`Toggle ${featureName}`}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Next quests — grayed/locked until the first evaluation. */}
        <div
          className={`onboarding-single__quests${
            connected ? '' : ' onboarding-single__quests--locked'
          }`}
        >
          {!connected && (
            <div className='onboarding-single__quests-lock text-muted d-flex align-items-center gap-1'>
              <Icon name='lock' width={12} fill='var(--color-icon-secondary)' />
              Unlocks after your first evaluation
            </div>
          )}
          <div className='onboarding-single__quests-title text-default fw-semibold'>
            Choose your next quest
          </div>
          <div className='onboarding-single__quests-sub text-muted'>
            Your flag is a kill-switch today — level it up whenever you’re
            ready. Same flag, no new setup.
          </div>
          <div className='onboarding-single__quests-grid'>
            {QUESTS.map((quest) => (
              <div
                key={quest.key}
                className='onboarding-single__quest rounded-md border border-default bg-surface-default'
              >
                <div className='onboarding-single__quest-title text-default fw-semibold'>
                  {quest.title}
                </div>
                <div className='onboarding-single__quest-desc text-muted'>
                  {quest.desc}
                </div>
                <div className='onboarding-single__quest-visual'>
                  {questVisual(quest.key)}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className='onboarding-single__skip d-flex justify-content-end'>
          <Button theme='text' onClick={onGoToDashboard}>
            Skip onboarding, I’m a pro →
          </Button>
        </div>
      </div>
    </div>
  )
}

OnboardingSinglePage.displayName = 'OnboardingSinglePage'

export default OnboardingSinglePage
