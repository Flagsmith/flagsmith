import React, { FC, useState } from 'react'
import classNames from 'classnames'
import CodeCard from './CodeCard'
import SdkPicker from './SdkPicker'
import { getSdkSnippet } from './sdkSnippets'
import { SDK_LANGS, SdkLang } from './sdkLangs'

type PackageManager = 'npm' | 'yarn'

const PACKAGE_MANAGERS: PackageManager[] = ['npm', 'yarn']

export type ConnectYourCodePanelProps = {
  environmentKey: string
  featureName: string
  onCopyInstall?: () => void
  onCopyWire?: () => void
}

// "Connect your code" tab: pick an SDK, then copy the install + wire snippets,
// pre-filled with the real env key and flag this onboarding created. The copy
// actions feed the verify checklist.
const ConnectYourCodePanel: FC<ConnectYourCodePanelProps> = ({
  environmentKey,
  featureName,
  onCopyInstall,
  onCopyWire,
}) => {
  const [sdkLang, setSdkLang] = useState<SdkLang>(SDK_LANGS[0])
  const [installPm, setInstallPm] = useState<PackageManager>('npm')

  const sdkSnippet = getSdkSnippet(sdkLang, environmentKey, featureName)
  const installCode =
    sdkSnippet.installYarn && installPm === 'yarn'
      ? sdkSnippet.installYarn
      : sdkSnippet.install

  return (
    <>
      <SdkPicker selected={sdkLang} onSelect={setSdkLang} />
      <div>
        <div className='onboarding-connect__step-head d-flex align-items-center gap-2 mb-2'>
          <span className='onboarding-connect__step-num'>1</span>
          <span className='text-default fw-semibold'>Install the SDK</span>
        </div>
        <CodeCard
          code={installCode}
          language='bash'
          onCopy={onCopyInstall}
          copyLabel='Copy install command'
          headerLeft={
            sdkSnippet.installYarn ? (
              <div className='onboarding-connect__pm d-inline-flex'>
                {PACKAGE_MANAGERS.map((pm) => (
                  <button
                    key={pm}
                    type='button'
                    className={classNames('onboarding-connect__pm-opt', {
                      'onboarding-connect__pm-opt--active': installPm === pm,
                    })}
                    onClick={() => setInstallPm(pm)}
                  >
                    {pm}
                  </button>
                ))}
              </div>
            ) : (
              <span className='onboarding-connect__codecard-lang'>
                {sdkLang.label}
              </span>
            )
          }
        />
      </div>
      <div>
        <div className='onboarding-connect__step-head d-flex align-items-center gap-2 mb-2'>
          <span className='onboarding-connect__step-num'>2</span>
          <span className='text-default fw-semibold'>
            Wire it in &amp; take instant control of what users see
          </span>
        </div>
        <CodeCard
          code={sdkSnippet.wire}
          language={sdkSnippet.language}
          onCopy={onCopyWire}
          copyLabel='Copy code snippet'
          headerLeft={
            <span className='onboarding-connect__codecard-lang'>
              {sdkLang.label}
            </span>
          }
        />
      </div>
    </>
  )
}

export default ConnectYourCodePanel
