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
      body: 'Flag serving and admin access are paused until usage drops below your limit or you upgrade. This page stays available so you can see what happened.',
      title: 'Your organisation is restricted',
      tone: 'danger',
    }
  }
  if (view.grace === 'countdown') {
    return {
      action: 'Upgrade plan',
      body: `You are over your plan limit. Flag serving pauses in ${
        view.graceDaysLeft ?? 0
      } days unless usage drops back under the limit.`,
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
