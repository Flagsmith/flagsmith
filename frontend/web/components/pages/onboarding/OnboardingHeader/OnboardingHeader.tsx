import React, { FC } from 'react'
import { sanitizeFeatureName } from 'common/utils/sanitizeFeatureName'
import EditableChip from 'components/pages/onboarding/EditableChip'
import './OnboardingHeader.scss'

export type OnboardingHeaderProps = {
  organisationName: string
  projectName: string
  featureName: string
  // Project enforces lower-case feature names — feeds the flag-name normaliser.
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
      <EditableChip
        label='Flag'
        value={featureName}
        transform={(raw) => sanitizeFeatureName(raw, caseSensitive)}
        onCommit={(name) => onRenameFeature?.(name)}
      />
    </p>
  </header>
)

export default OnboardingHeader
