import React, { FC } from 'react'
import Link from 'components/base/link'
import Button from 'components/base/forms/Button'

export type OnboardingAlreadySetUpProps = {
  projectName: string
  // Where to send them to carry on with their own flags.
  featuresHref: string
  onSkip: () => void
}

// Shown when the tour has nothing to teach with: the project already has flags,
// so we seed no demo flag (see ensureFlag) and there is no point walking someone
// through connecting a project that is already connected.
const OnboardingAlreadySetUp: FC<OnboardingAlreadySetUpProps> = ({
  featuresHref,
  onSkip,
  projectName,
}) => (
  <div className='onboarding-flow mx-auto text-center'>
    <h2 className='mb-2'>You&apos;re already set up</h2>
    <p className='text-muted mb-3'>
      {projectName} already has flags, so we haven&apos;t added a demo one.
    </p>
    <div className='d-flex justify-content-center align-items-center gap-3'>
      <Button onClick={onSkip}>Go to your projects</Button>
      <Link to={featuresHref}>View flags in {projectName}</Link>
    </div>
  </div>
)

export default OnboardingAlreadySetUp
