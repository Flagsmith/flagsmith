import { FC } from 'react'
import Constants from 'common/constants'
import { Button } from 'components/base/forms/Button'
import { UsageView } from './types'

type UsageBannerProps = {
  view: UsageView
}

type Banner = {
  tone: 'warning' | 'danger'
  title: string
  body: string
  action?: string
}

const bannerFor = (view: UsageView): Banner | null => {
  if (view.restricted) {
    return {
      action: 'Upgrade plan',
      body: view.restrictedImmediately
        ? `You went over your free plan limit again. Your grace period was already used, so flag serving was paused straight away rather than after 7 days.${
            view.resumesAt
              ? ` Service resumes on ${view.resumesAt} if usage stays below the limit, or immediately if you upgrade.`
              : ''
          }`
        : 'Flag serving and admin access are paused until usage drops below your limit or you upgrade. This page stays available so you can see what happened.',
      title: 'Your organisation is restricted',
      tone: 'danger',
    }
  }
  if (view.grace === 'not-applied') {
    return {
      action: 'Upgrade plan',
      body: 'Above 200% of your plan limit the grace period does not apply, so overage is charged for this billing period.',
      title: 'Your organisation is more than 200% over its plan limit',
      tone: 'danger',
    }
  }
  if (view.grace === 'countdown') {
    return {
      action: 'Upgrade plan',
      // The 7 days is a notification period rather than a consumable grace:
      // every organisation that crosses 100% gets it, every time. The exact
      // days left need the notification date, which is not exposed yet.
      body: view.graceDaysLeft
        ? `You are over your plan limit. Flag serving pauses in ${view.graceDaysLeft} days unless usage drops back under the limit.`
        : 'You are over your plan limit. You have 7 days to bring usage back under it before flag serving pauses.',
      title: 'Your organisation is over its plan limit',
      tone: 'warning',
    }
  }
  if (view.grace === 'covering') {
    return {
      body: 'This month is covered by your grace period, so there is no overage charge. Any future billing periods that exceed your plan limits will be charged.',
      title: 'Your organisation is over its plan limit',
      tone: 'warning',
    }
  }
  if (view.grace === 'used') {
    return {
      action: 'Upgrade plan',
      body: 'Usage above your plan limit is charged as overage. Upgrading raises the limit and stops the charges.',
      title: 'Your organisation has exceeded its plan limit',
      tone: 'danger',
    }
  }
  return null
}

/** PROTOTYPE (#8184). The over-limit and restricted headers from S2 and S4. */
const UsageBanner: FC<UsageBannerProps> = ({ view }) => {
  const banner = bannerFor(view)
  if (!banner) {
    return null
  }

  return (
    <div className={`usage-proto__banner usage-proto__banner--${banner.tone}`}>
      <div>
        <div className='usage-proto__banner-title'>{banner.title}</div>
        <div className='usage-proto__banner-body'>{banner.body}</div>
      </div>
      {banner.action && (
        <Button
          onClick={() => {
            document.location.replace(Constants.getUpgradeUrl('usage'))
          }}
        >
          {banner.action}
        </Button>
      )}
    </div>
  )
}

export default UsageBanner
