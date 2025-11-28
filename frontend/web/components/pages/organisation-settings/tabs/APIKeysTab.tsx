import React from 'react'
import AdminAPIKeys from 'components/AdminAPIKeys'

type APIKeysTabProps = {
  organisationId: number
}

export const APIKeysTab = ({ organisationId }: APIKeysTabProps) => {
  return <AdminAPIKeys organisationId={organisationId} />
}
