import React, { FC } from 'react'
import Icon from 'components/icons/Icon'

export const ROLLOUT_GUIDE_URL =
  'https://docs.flagsmith.com/managing-flags/rollout/rollout-by-percentage'

export const getRolloutSteps = (
  featureName: string,
): { title: string; body: string }[] => [
  {
    body: 'Add a “Percentage split” rule and set your starting share, e.g. 10% of users.',
    title: 'Create a segment',
  },
  {
    body: `Turn ${featureName} on for that segment, so only those users get it.`,
    title: 'Override the flag',
  },
  {
    body: 'Raise the percentage as your confidence grows: 10% → 25% → 50% → 100%.',
    title: 'Increase over time',
  },
]

// Sits with the steps rather than in docs: without it the override reaches
// nobody and the user has no way to tell.
export const RolloutPrerequisite: FC = () => (
  <p className='onboarding-rollout-quest__prerequisite text-secondary d-flex gap-2 m-0'>
    <Icon name='info' width={14} className='icon-secondary' />
    <span>
      Percentage splits only apply to users you identify. If your app doesn’t
      call <code>flagsmith.identify(...)</code> yet, add it first, or everyone
      keeps getting the same value.
    </span>
  </p>
)
