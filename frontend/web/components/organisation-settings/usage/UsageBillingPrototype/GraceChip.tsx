import { FC } from 'react'
import Tooltip from 'components/Tooltip'
import UsageBadge, { BadgeTone } from './UsageBadge'
import { GraceState } from './types'

type GraceChipProps = {
  grace: GraceState
}

const TONE: Record<GraceState, BadgeTone> = {
  available: 'success',
  countdown: 'warning',
  covering: 'info',
  restricted: 'danger',
  used: 'danger',
}

const LABEL: Record<GraceState, string> = {
  available: 'Grace period: available',
  countdown: 'Grace period: ending soon',
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
const GraceChip: FC<GraceChipProps> = ({ grace }) => (
  <Tooltip title={<UsageBadge tone={TONE[grace]}>{LABEL[grace]}</UsageBadge>}>
    {EXPLANATION[grace]}
  </Tooltip>
)

export default GraceChip
