import { FC } from 'react'
import Tooltip from 'components/Tooltip'
import { GraceState } from './types'

type GraceChipProps = {
  grace: GraceState
  daysLeft?: number
}

const TONE: Record<GraceState, string> = {
  available: 'success',
  countdown: 'warning',
  covering: 'info',
  restricted: 'danger',
  used: 'danger',
}

const LABEL: Record<GraceState, string> = {
  available: 'Grace period: available',
  countdown: 'Grace period: ending',
  covering: 'Grace period: covering this period',
  restricted: 'Restricted',
  used: 'Grace period: used',
}

const EXPLANATION: Record<GraceState, string> = {
  available:
    'Your first month over the limit is covered. We never cut off your API without warning.',
  countdown:
    'You are over your limit. Flag serving pauses when the grace window ends, unless usage drops back under.',
  covering:
    'You are over your limit, but this month is covered by your grace period, so there is no overage charge.',
  restricted:
    'The grace window has passed. Flag serving and admin access are paused, but this page stays readable.',
  used: 'Your grace period has already been used, so usage above the limit is charged as overage.',
}

/** PROTOTYPE (#8184). Grace period status, per the "Grace period states" design. */
const GraceChip: FC<GraceChipProps> = ({ daysLeft, grace }) => {
  const label =
    grace === 'countdown' && daysLeft ? `${daysLeft} days left` : LABEL[grace]

  return (
    <Tooltip
      title={
        <span className={`usage-proto__chip usage-proto__chip--${TONE[grace]}`}>
          {label}
        </span>
      }
    >
      {EXPLANATION[grace]}
    </Tooltip>
  )
}

export default GraceChip
