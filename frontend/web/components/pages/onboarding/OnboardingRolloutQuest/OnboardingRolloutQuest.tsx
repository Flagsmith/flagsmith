import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import RolloutComingSoonCard from './RolloutComingSoonCard'
import {
  ROLLOUT_GUIDE_URL,
  RolloutPrerequisite,
  getRolloutSteps,
} from './rolloutSteps'
import './OnboardingRolloutQuest.scss'

export type OnboardingRolloutQuestProps = {
  featureName: string
  onContinue: () => void
  onDismiss: () => void
  onNotifyMe: () => void
  onFeedback: () => void
}

const OnboardingRolloutQuest: FC<OnboardingRolloutQuestProps> = ({
  featureName,
  onContinue,
  onDismiss,
  onFeedback,
  onNotifyMe,
}) => (
  <div className='onboarding-rollout-quest p-4 d-flex flex-column gap-4'>
    <p className='onboarding-rollout-quest__body text-secondary m-0'>
      Release {featureName} to a growing percentage of your users.
    </p>

    <section className='onboarding-rollout-quest__card bg-surface-default border-default rounded-xl d-flex flex-column gap-3'>
      <h3 className='onboarding-rollout-quest__card-title m-0 fw-bold text-default'>
        How to roll out gradually today
      </h3>
      <ol className='onboarding-rollout-quest__steps d-flex flex-column gap-3 m-0 p-0'>
        {getRolloutSteps(featureName).map((step, index) => (
          <li key={step.title} className='d-flex gap-3'>
            <span className='onboarding-rollout-quest__step-number bg-surface-action-subtle text-action rounded-full d-flex align-items-center justify-content-center flex-shrink-0'>
              {index + 1}
            </span>
            <span className='d-flex flex-column gap-1'>
              <span className='onboarding-rollout-quest__step-title fw-bold text-default'>
                {step.title}
              </span>
              <span className='onboarding-rollout-quest__body text-secondary'>
                {step.body}
              </span>
            </span>
          </li>
        ))}
      </ol>
      <RolloutPrerequisite />
      <Button
        theme='text'
        href={ROLLOUT_GUIDE_URL}
        target='_blank'
        className='align-self-start'
      >
        <span className='d-inline-flex align-items-center gap-2'>
          <Icon name='file-text' width={14} />
          Read the gradual rollout guide
        </span>
      </Button>
    </section>

    <RolloutComingSoonCard onNotifyMe={onNotifyMe} onFeedback={onFeedback} />

    <div className='d-flex align-items-center gap-3'>
      <Button onClick={onContinue}>
        <span className='d-inline-flex align-items-center gap-2'>
          <Icon name='layers' width={14} />
          Create a rollout segment
        </span>
      </Button>
      <Button theme='text' onClick={onDismiss}>
        Maybe later
      </Button>
    </div>
  </div>
)

export default OnboardingRolloutQuest
