import React, { FC } from 'react'
import Lottie from 'lottie-react'
import settingUpAnimation from './settingUpAnimation.json'
import './OnboardingLoading.scss'

const OnboardingLoading: FC = () => (
  <div className='onboarding-loading'>
    <Lottie
      className='onboarding-loading__anim'
      animationData={settingUpAnimation}
      loop
      aria-hidden
    />
    <span className='onboarding-loading__text'>Setting up your workspace…</span>
  </div>
)

export default OnboardingLoading
