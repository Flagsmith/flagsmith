import React, { FC, useState } from 'react'
import OnboardingTabs, {
  OnboardingTab,
  OnboardingTabPanel,
} from 'components/pages/onboarding/OnboardingTabs'
import ConnectWithAiPanel from './ConnectWithAiPanel'
import ConnectYourCodePanel from './ConnectYourCodePanel'
import './OnboardingConnectPanel.scss'

type ConnectTab = 'manual' | 'ai'

const CONNECT_TABS: OnboardingTab<ConnectTab>[] = [
  { id: 'manual', label: 'Connect your code' },
  {
    alignEnd: true,
    id: 'ai',
    label: (
      <>
        <span className='text-action' aria-hidden>
          ✦
        </span>{' '}
        Connect with AI
      </>
    ),
  },
]

export type OnboardingConnectPanelProps = {
  environmentKey: string
  featureName: string
  onCopyInstall?: () => void
  onCopyWire?: () => void
}

// Two ways to connect an app to the pre-created flag: paste an agent-agnostic
// prompt ("Connect with AI"), or copy the install + wire snippets for a chosen
// SDK ("Connect your code"). Both carry the real env key + flag; nothing faked.
// This is the shell - the tabs and each panel's content live in their own files.
const OnboardingConnectPanel: FC<OnboardingConnectPanelProps> = ({
  environmentKey,
  featureName,
  onCopyInstall,
  onCopyWire,
}) => {
  const [tab, setTab] = useState<ConnectTab>('manual')

  return (
    <div className='onboarding-connect rounded-lg shadow-md bg-surface-subtle'>
      <OnboardingTabs
        aria-label='Connect your app'
        tabs={CONNECT_TABS}
        activeId={tab}
        onChange={setTab}
      />

      <OnboardingTabPanel
        tabId='ai'
        active={tab === 'ai'}
        className='onboarding-connect__panel d-flex flex-column gap-3'
      >
        <ConnectWithAiPanel
          environmentKey={environmentKey}
          featureName={featureName}
        />
      </OnboardingTabPanel>

      <OnboardingTabPanel
        tabId='manual'
        active={tab === 'manual'}
        className='onboarding-connect__panel d-flex flex-column gap-4'
      >
        <ConnectYourCodePanel
          environmentKey={environmentKey}
          featureName={featureName}
          onCopyInstall={onCopyInstall}
          onCopyWire={onCopyWire}
        />
      </OnboardingTabPanel>
    </div>
  )
}

export default OnboardingConnectPanel
