import React, { FC } from 'react'

import { Environment, SegmentMembership } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'
import Tooltip from 'components/Tooltip'
import UsersIcon from 'components/icons/UsersIcon'

const shortAgo = (iso: string): string => {
  const diffSec = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000))
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.round(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.round(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  return `${Math.round(diffHr / 24)}d ago`
}

const formatTooltip = (count: number, lastSyncedAt: string | undefined): string => {
  const noun = count === 1 ? 'identity' : 'identities'
  const base = `${count} ${noun}`
  return lastSyncedAt ? `${base} — last synced ~${shortAgo(lastSyncedAt)}` : base
}

type ChipProps = {
  count: number
  dataTest?: string
  tooltip: string
}

const Chip: FC<ChipProps> = ({ count, dataTest, tooltip }) => (
  <Tooltip
    plainText
    title={
      <span
        className='chip chip--xs bg-primary text-white ms-3'
        style={{ border: 'none', alignSelf: 'center', verticalAlign: 'middle' }}
        data-test={dataTest}
      >
        <UsersIcon className='chip-svg-icon' />
        <span>{count}</span>
      </span>
    }
  >
    {tooltip}
  </Tooltip>
)

type TotalProps = {
  memberships: SegmentMembership[] | undefined
}

export const SegmentMembershipTotalBadge: FC<TotalProps> = ({ memberships }) => {
  if (!memberships?.length) {
    return null
  }
  const total = memberships.reduce((sum, m) => sum + m.count, 0)
  const latest = memberships.reduce(
    (acc, m) => (!acc || m.last_synced_at > acc ? m.last_synced_at : acc),
    '',
  )
  return (
    <Chip
      count={total}
      tooltip={formatTooltip(total, latest || undefined)}
      dataTest='segment-membership-total'
    />
  )
}

type EnvProps = {
  membership: SegmentMembership
  environment?: Environment
}

export const SegmentMembershipEnvBadge: FC<EnvProps> = ({
  environment,
  membership,
}) => {
  const envs = (ProjectStore.getEnvs() as Environment[] | null) || []
  const env = environment ?? envs.find((e) => e.id === membership.environment)
  if (!env) {
    return null
  }
  return (
    <Chip
      count={membership.count}
      tooltip={formatTooltip(membership.count, membership.last_synced_at)}
      dataTest={`segment-membership-${env.api_key}`}
    />
  )
}
