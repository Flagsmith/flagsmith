import { FC } from 'react'
import { AuditLogDetail } from 'common/types/responses'
import Format from 'common/utils/format'
import DiffEnabled from 'components/diff/DiffEnabled'
import DiffString from 'components/diff/DiffString'
import Link from 'components/base/link'
import PlanBasedBanner from 'components/PlanBasedAccess'
import {
  getAuditLogRelatedObjectLink,
  isAuditLogVersionLocked,
} from './getAuditLogRelatedObjectLink'

type AuditLogChangesProps = {
  item: AuditLogDetail
  // The plan's feature history limit, from subscription metadata.
  versionLimitDays?: number | null
}

// Same field rendering as AuditLogItemPage, so both read alike until it goes.
const AuditLogChanges: FC<AuditLogChangesProps> = ({
  item,
  versionLimitDays,
}) => {
  const changes = item.change_details
  if (!changes.length) {
    if (isAuditLogVersionLocked(item, versionLimitDays)) {
      return (
        <div className='d-flex align-items-center gap-2 fs-small text-secondary'>
          Version history is limited to {versionLimitDays} days on your plan.
          <PlanBasedBanner force feature='VERSIONING_DAYS' theme='badge' />
        </div>
      )
    }
    const link = getAuditLogRelatedObjectLink(item)
    if (link) {
      return (
        <Link className='fs-small' to={link.to}>
          {link.label}
        </Link>
      )
    }
    return (
      <p className='text-secondary fs-small mb-0'>No field changes recorded.</p>
    )
  }
  return (
    <dl className='d-flex flex-column gap-2 mb-0'>
      {changes.map((change) => (
        <div
          key={change.field}
          className='d-flex flex-wrap align-items-center gap-2'
        >
          <dt className='text-secondary fs-small fw-semibold'>
            {Format.camelCase(Format.enumeration.get(change.field))}
          </dt>
          <dd className='mb-0 mw-100 overflow-auto'>
            {change.field === 'enabled' ? (
              <DiffEnabled oldValue={!!change.old} newValue={!!change.new} />
            ) : (
              <DiffString oldValue={change.old} newValue={change.new} />
            )}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export default AuditLogChanges
