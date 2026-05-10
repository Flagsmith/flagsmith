import React, { FC } from 'react'

import { SegmentMembership } from 'common/types/responses'
import UsersIcon from 'components/icons/UsersIcon'

const sumCounts = (memberships: SegmentMembership[]): number =>
  memberships.reduce((sum, m) => sum + m.count, 0)

const identityNoun = (count: number): string =>
  count === 1 ? 'identity' : 'identities'

type TotalProps = {
  memberships: SegmentMembership[] | undefined
}

export const SegmentMembershipTotalBadge: FC<TotalProps> = ({
  memberships,
}) => {
  if (!memberships?.length) {
    return null
  }
  const total = sumCounts(memberships)
  return (
    <span
      className='chip chip--xs chip--filled ms-2'
      data-test='segment-membership-total'
    >
      <UsersIcon className='chip-svg-icon' />
      <span>
        {total} {identityNoun(total)}
      </span>
    </span>
  )
}

export const SegmentMembershipTabCount: FC<TotalProps> = ({ memberships }) => {
  if (!memberships?.length) {
    return null
  }
  return (
    <span
      className='ms-2 text-muted fw-normal'
      data-test='segment-membership-total'
    >
      ({sumCounts(memberships)})
    </span>
  )
}

type EnvProps = {
  membership: SegmentMembership
  envApiKey: string
}

export const SegmentMembershipEnvCount: FC<EnvProps> = ({
  envApiKey,
  membership,
}) => (
  <span
    className='text-muted fs-small ms-auto ps-2'
    data-test={`segment-membership-${envApiKey}`}
  >
    {membership.count} {identityNoun(membership.count)}
  </span>
)
