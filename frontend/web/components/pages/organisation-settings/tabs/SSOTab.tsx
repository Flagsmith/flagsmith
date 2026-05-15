import React from 'react'
import PlanBasedBanner from 'components/PlanBasedAccess'
import SamlTab from 'components/SamlTab'
import ScimSection from 'components/ScimSection'

type SSOTabProps = {
  organisationId: number
}

export const SSOTab = ({ organisationId }: SSOTabProps) => {
  return (
    <PlanBasedBanner feature='SAML' theme='page'>
      <SamlTab organisationId={organisationId} />
      <ScimSection organisationId={organisationId} />
    </PlanBasedBanner>
  )
}
