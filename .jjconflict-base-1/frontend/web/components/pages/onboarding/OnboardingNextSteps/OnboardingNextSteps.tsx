import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon from 'components/icons/Icon'
import SelectableCard from 'components/base/SelectableCard/SelectableCard'
import './OnboardingNextSteps.scss'

export type OnboardingNextStep = 'rollout' | 'experiment' | 'remote-config'

export type OnboardingNextStepsProps = {
  // Locked (dimmed, non-interactive) until the app connects, like the flags
  // table - the steps only make sense once the flag is live.
  locked: boolean
  onSelect: (step: OnboardingNextStep) => void
}

// A 25%-filled track: "ship to a % of your users".
const RolloutPreview: FC = () => (
  <span className='onboarding-next-steps__track'>
    <span className='onboarding-next-steps__track-fill' />
  </span>
)

// An A/B segmented control, A selected.
const ExperimentPreview: FC = () => (
  <span className='onboarding-next-steps__segmented d-inline-flex'>
    <span className='onboarding-next-steps__segment onboarding-next-steps__segment--active'>
      A
    </span>
    <span className='onboarding-next-steps__segment'>B</span>
  </span>
)

// A value chip: "serve a value, not just on/off".
const RemoteConfigPreview: FC = () => (
  <span className='onboarding-next-steps__value-pill bg-surface-action-subtle text-action'>
    {'"theme": "dark"'}
  </span>
)

const STEPS: {
  key: OnboardingNextStep
  title: string
  description: string
  preview: ReactNode
  caption?: string
}[] = [
  {
    caption: '25% of users',
    description: 'Ship to a % of your users.',
    key: 'rollout',
    preview: <RolloutPreview />,
    title: 'Gradual rollout',
  },
  {
    description: 'A/B test which variant wins.',
    key: 'experiment',
    preview: <ExperimentPreview />,
    title: 'Experiment',
  },
  {
    description: 'Serve a value, not just on/off.',
    key: 'remote-config',
    preview: <RemoteConfigPreview />,
    title: 'Remote config',
  },
]

// "Choose your next quest": the three ways the demo flag can level up, each
// linking to its real config (the page owns where). Locked until the app
// connects.
const OnboardingNextSteps: FC<OnboardingNextStepsProps> = ({
  locked,
  onSelect,
}) => (
  <section className='onboarding-next-steps d-flex flex-column gap-2'>
    {locked && (
      <span className='onboarding-next-steps__lock d-flex align-items-center gap-1'>
        <Icon name='lock' width={13} />
        Unlocks after your first evaluation
      </span>
    )}
    <div
      className={cn('d-flex flex-column gap-3', {
        'onboarding-next-steps__body--locked': locked,
      })}
      inert={locked || undefined}
    >
      <div className='d-flex flex-column gap-1'>
        <h3 className='onboarding-next-steps__title m-0 fw-bold text-default'>
          Choose your next quest
        </h3>
        <p className='onboarding-next-steps__subtitle m-0'>
          You&apos;ve built a basic on/off feature toggle. The same flag can
          evolve into any of these, no new code, just configuration.
        </p>
      </div>
      <div className='onboarding-next-steps__row d-flex gap-3'>
        {STEPS.map((step) => (
          <SelectableCard
            key={step.key}
            title={step.title}
            description={step.description}
            onClick={() => onSelect(step.key)}
          >
            <span className='onboarding-next-steps__preview d-flex flex-column gap-2'>
              {step.preview}
              {step.caption && (
                <span className='onboarding-next-steps__caption'>
                  {step.caption}
                </span>
              )}
            </span>
          </SelectableCard>
        ))}
      </div>
    </div>
  </section>
)

export default OnboardingNextSteps
