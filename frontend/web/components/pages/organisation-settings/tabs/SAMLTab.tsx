import React from 'react'
import SamlTab from 'components/SamlTab'

type SAMLTabProps = {
  organisationId: number
}

export const SAMLTab = ({ organisationId }: SAMLTabProps) => {
  return <SamlTab organisationId={organisationId} />
}
