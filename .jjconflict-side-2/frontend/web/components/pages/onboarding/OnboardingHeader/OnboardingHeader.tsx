import React, { FC } from 'react'
import Constants from 'common/constants'
import { sanitizeFeatureName } from 'common/utils/sanitizeFeatureName'
import InlineInput from 'components/pages/onboarding/InlineInput'
import './OnboardingHeader.scss'

export type OnboardingHeaderProps = {
  organisationName: string
  projectName: string
  featureName: string
  // Project enforces lower-case feature names - feeds the flag-name normaliser.
  caseSensitive: boolean
  onRenameOrganisation?: (name: string) => void
  onRenameProject?: (name: string) => void
  onRenameFeature?: (name: string) => void
}

const OnboardingHeader: FC<OnboardingHeaderProps> = ({
  caseSensitive,
  featureName,
  onRenameFeature,
  onRenameOrganisation,
  onRenameProject,
  organisationName,
  projectName,
}) => (
  <header className='onboarding-header'>
    <div className='onboarding-header__crumb text-muted'>
      Onboarding / Connect your app
    </div>
    <h1 className='onboarding-header__title mb-0'>
      Welcome, let’s get you live 👋
    </h1>
    <p className='onboarding-header__subtitle text-muted mb-0'>
      We created your organisation{' '}
      <InlineInput
        label='Organisation'
        value={organisationName}
        onCommit={(name) => onRenameOrganisation?.(name)}
      />
      , your project{' '}
      <InlineInput
        label='Project'
        value={projectName}
        onCommit={(name) => onRenameProject?.(name)}
      />{' '}
      and your flag{' '}
      <InlineInput
        label='Flag'
        value={featureName}
        variant='accent'
        maxLength={Constants.forms.maxLength.FEATURE_ID}
        transform={(raw) => sanitizeFeatureName(raw, caseSensitive)}
        onCommit={(name) => onRenameFeature?.(name)}
      />
    </p>
  </header>
)

export default OnboardingHeader
