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
  <div className='onboarding-rollout-quest d-flex flex-column gap-4'>
    <p className='fs-caption lh-sm text-secondary m-0'>
      Release {featureName} to a growing percentage of your users.
    </p>

    <section className='onboarding-rollout-quest__card bg-surface-muted rounded-xl p-4 d-flex flex-column gap-3'>
      <h6 className='m-0'>How to roll out gradually today</h6>
      <ol className='list-unstyled d-flex flex-column gap-3 m-0'>
        {getRolloutSteps(featureName).map((step, index) => (
          <li key={step.title} className='d-flex gap-3'>
            <span className='onboarding-rollout-quest__step-number bg-surface-action-subtle text-action rounded-full fs-captionSmall fw-bold d-flex align-items-center justify-content-center flex-shrink-0'>
              {index + 1}
            </span>
            <span className='d-flex flex-column gap-1'>
              <span className='fw-bold text-default'>{step.title}</span>
              <span className='fs-caption lh-sm text-secondary'>
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
        <Icon name='file-text' width={14} />
        Read the gradual rollout guide
      </Button>
    </section>

    <RolloutComingSoonCard onNotifyMe={onNotifyMe} onFeedback={onFeedback} />

    <div className='d-flex align-items-center gap-3'>
      <Button onClick={onContinue}>
        <Icon name='layers' width={14} />
        Create a rollout segment
      </Button>
      <Button theme='text' onClick={onDismiss}>
        Maybe later
      </Button>
    </div>
  </div>
)

export default OnboardingRolloutQuest
