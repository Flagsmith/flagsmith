import { FC } from 'react'
import { AuditLogItem } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import { getAuditLogTypeIcon } from 'components/audit-log/auditLogType'
import './AuditLogRow.scss'

const AuditLogTypeIcon: FC<{ item: AuditLogItem }> = ({ item }) => (
  <span
    aria-hidden
    className='audit-log-row__type d-flex align-items-center justify-content-center flex-shrink-0 rounded-full bg-surface-muted icon-secondary'
  >
    <Icon name={getAuditLogTypeIcon(item)} width={16} />
  </span>
)

export default AuditLogTypeIcon
