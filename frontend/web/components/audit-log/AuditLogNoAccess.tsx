import { FC } from 'react'
import EmptyState from 'components/EmptyState'

const AuditLogNoAccess: FC = () => (
  <EmptyState
    icon='lock'
    title="You don't have access to this audit log"
    description='Only organisation admins can see it.'
  />
)

export default AuditLogNoAccess
