import React from 'react'
import LicensingTabContent from 'components/LicensingTabContent'

type LicensingTabProps = {
  organisationId: number
}

export const LicensingTab = ({ organisationId }: LicensingTabProps) => {
  return <LicensingTabContent organisationId={organisationId} />
}
