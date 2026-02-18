import React from 'react'
import OidcTab from 'components/OidcTab'

type OIDCTabProps = {
  organisationId: number
}

export const OIDCTab = ({ organisationId }: OIDCTabProps) => {
  return <OidcTab organisationId={organisationId} />
}
