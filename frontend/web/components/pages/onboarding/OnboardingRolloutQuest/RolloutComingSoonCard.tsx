import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'

export const ROLLOUT_FEEDBACK_URL =
  'mailto:support@flagsmith.com?subject=Gradual%20rollout'

export type RolloutComingSoonCardProps = {
  onNotifyMe: () => void
  onFeedback: () => void
}

// The one thing we don't ship yet: the three steps above in a single action. It
// promises a simpler flow, never the capability.
const RolloutComingSoonCard: FC<RolloutComingSoonCardProps> = ({
  onFeedback,
  onNotifyMe,
}) => {
  const [notified, setNotified] = useState(false)
  const notifyMe = () => {
    setNotified(true)
    onNotifyMe()
  }
  return (
    <section className='bg-surface-action-subtle rounded-xl p-4 d-flex flex-column gap-2'>
      {/* Accent rather than the design's solid purple: there is no inverse
          text token, and white on the dark-mode action surface is ~3.2:1. */}
      <Chip variant='accent' size='xs' className='align-self-start'>
        <Icon name='flash' width={12} />
        Coming soon
      </Chip>
      <h6 className='m-0'>We’re making gradual rollouts one-click</h6>
      <p className='onboarding-rollout-quest__body text-secondary m-0'>
        Soon you’ll ramp a flag up on a schedule automatically, without editing
        segments by hand. Want early access?
      </p>
      <div className='d-flex align-items-center gap-3'>
        {notified ? (
          <span className='fs-caption d-inline-flex align-items-center gap-2 text-action'>
            <Icon name='checkmark-circle' width={16} />
            Thanks, we’ll be in touch.
          </span>
        ) : (
          <Button onClick={notifyMe}>
            <Icon name='bell' width={14} />
            Notify me
          </Button>
        )}
        {/* No target: a mailto in a new tab leaves a blank tab behind. */}
        <Button theme='text' href={ROLLOUT_FEEDBACK_URL} onClick={onFeedback}>
          Tell us what you need
        </Button>
      </div>
    </section>
  )
}

export default RolloutComingSoonCard
