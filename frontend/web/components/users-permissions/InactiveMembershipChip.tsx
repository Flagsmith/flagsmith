import React, { FC } from 'react'
import Chip from 'components/base/Chip'
import Tooltip from 'components/Tooltip'
import { User } from 'common/types/responses'

export const INACTIVE_MEMBERSHIP_TOOLTIP =
  "This member's organisation membership has been deactivated by your identity provider. They cannot access this organisation, and do not count towards your seat limit. Their role, permissions and groups are retained."

type InactiveMembershipChipProps = {
  user: Pick<User, 'is_organisation_membership_active'> | undefined
}

// Flags users whose organisation membership was deactivated, e.g. via SCIM.
// Renders nothing unless the API explicitly reports an inactive membership,
// so it is safe to use with user payloads that omit the field.
// The chip carries no margin of its own: parents own the spacing, typically
// via `d-flex align-items-center gap-2`.
const InactiveMembershipChip: FC<InactiveMembershipChipProps> = ({ user }) => {
  if (user?.is_organisation_membership_active !== false) {
    return null
  }
  return (
    <Tooltip plainText delayShow={100} title={<Chip size='xs'>Inactive</Chip>}>
      {INACTIVE_MEMBERSHIP_TOOLTIP}
    </Tooltip>
  )
}

export default InactiveMembershipChip
