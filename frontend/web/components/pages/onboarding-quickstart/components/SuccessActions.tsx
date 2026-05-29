import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import { OnboardingRoleKey } from 'web/components/pages/onboarding-quickstart/data/roles'

type SuccessActionsProps = {
  canInvite: boolean
  onExplore: () => void
  onInvite: () => void
  role: OnboardingRoleKey
}

const COPY_BY_ROLE: Record<
  OnboardingRoleKey,
  {
    heading: string
    subtitle: string
    subtitleNoInvite: string
    inviteLabel: string
  }
> = {
  engineer: {
    heading: "Nice — you've shipped your first eval.",
    inviteLabel: 'Invite a teammate',
    subtitle:
      'Get the rest of your team in so they can target users and roll out gradually.',
    subtitleNoInvite:
      'Head to your dashboard to target users and roll out your flag gradually.',
  },
  // 'other' never reaches this component — they skip AHA — but typing it
  // here keeps the Record exhaustive in case the routing changes.
  other: {
    heading: "You're in.",
    inviteLabel: 'Invite a teammate',
    subtitle: 'Explore the dashboard or invite teammates when you’re ready.',
    subtitleNoInvite: 'Explore the dashboard whenever you’re ready.',
  },

  pm: {
    heading: 'Your dashboard is ready.',
    inviteLabel: 'Invite a teammate',
    subtitle:
      'Invite a teammate to wire Flagsmith into your codebase and ship the first flag.',
    subtitleNoInvite:
      'Explore the dashboard and wire Flagsmith into your codebase.',
  },
}

const SuccessActions: FC<SuccessActionsProps> = ({
  canInvite,
  onExplore,
  onInvite,
  role,
}) => {
  const copy = COPY_BY_ROLE[role]
  return (
    <div className='onboarding-quickstart__success rounded-lg border border-default bg-surface-subtle p-4 d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3'>
      <div>
        <h3 className='mb-1'>{copy.heading}</h3>
        <p className='text-muted mb-0'>
          {canInvite ? copy.subtitle : copy.subtitleNoInvite}
        </p>
      </div>
      <div className='d-flex flex-column flex-sm-row align-items-sm-center gap-2'>
        {canInvite && (
          <Button theme='primary' onClick={onInvite}>
            <span className='d-inline-flex align-items-center gap-1'>
              <Icon name='people' width={16} />
              {copy.inviteLabel}
            </span>
          </Button>
        )}
        {/* When invite is hidden, Explore is the only and primary CTA. */}
        <Button theme={canInvite ? 'text' : 'primary'} onClick={onExplore}>
          Explore the dashboard →
        </Button>
      </div>
    </div>
  )
}

export default SuccessActions
