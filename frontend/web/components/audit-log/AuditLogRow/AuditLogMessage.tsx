import { FC } from 'react'
import moment from 'moment'
import { AuditLogItem } from 'common/types/responses'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import Chip from 'components/base/Chip'
import { getAuditLogTypeLabel } from 'components/audit-log/auditLogType'
import './AuditLogRow.scss'

const AuditLogMessage: FC<{ item: AuditLogItem }> = ({ item }) => {
  const author = item.is_system_event
    ? 'System'
    : getUserDisplayName(item.author ?? undefined)
  return (
    <span className='audit-log-row__message gap-1'>
      <span className='text-default fw-semibold'>{item.log}</span>
      <span className='d-flex align-items-center gap-2 text-secondary fs-small'>
        <Chip size='xs'>{getAuditLogTypeLabel(item)}</Chip>
        {author} · {moment(item.created_date).format('HH:mm')}
      </span>
    </span>
  )
}

export default AuditLogMessage
