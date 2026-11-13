import { FC } from 'react'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import AuditLogNoAccess from 'components/audit-log/AuditLogNoAccess'
import { getAuditLogErrorKind } from 'components/audit-log/auditLogError'

type AuditLogListErrorProps = {
  error: unknown
  onRetry: () => void
}

const AuditLogListError: FC<AuditLogListErrorProps> = ({ error, onRetry }) => {
  const kind = getAuditLogErrorKind(error)
  if (kind === 'forbidden') return <AuditLogNoAccess />
  return (
    <Banner
      type='error'
      action={
        <Button theme='outline' size='small' onClick={onRetry}>
          Try again
        </Button>
      }
    >
      {kind === 'timeout'
        ? 'This search took too long. Try a more specific term.'
        : "Couldn't load the audit log."}
    </Banner>
  )
}

export default AuditLogListError
