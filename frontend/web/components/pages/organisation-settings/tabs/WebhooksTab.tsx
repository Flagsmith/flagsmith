import React from 'react'
import AuditLogWebhooks from 'components/modals/AuditLogWebhooks'

type WebhooksTabProps = {
  organisationId: number
}

export const WebhooksTab = ({ organisationId }: WebhooksTabProps) => {
  return (
    <FormGroup className='mt-4'>
      <AuditLogWebhooks organisationId={organisationId} />
    </FormGroup>
  )
}
