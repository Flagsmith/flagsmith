import React, { FC } from 'react'
import Lottie from 'lottie-react'
import settingUpAnimation from 'web/components/pages/onboarding-quickstart/settingUpAnimation.json'

// The "setting up your workspace" screen shown while the onboarding resources
// (org/project/envs/flag) are created. Lazy-loaded by the container so
// lottie-web + the animation JSON only download when this screen actually
// renders — keeping them out of the page's initial bundle.
const OnboardingLoading: FC = () => (
  <div className='onboarding-single'>
    <div className='onboarding-single__page onboarding-single__loading'>
      <Lottie
        className='onboarding-single__loading-anim'
        animationData={settingUpAnimation}
        loop
        aria-hidden
      />
      <span className='text-muted'>Setting up your workspace…</span>
    </div>
  </div>
)

export default OnboardingLoading
