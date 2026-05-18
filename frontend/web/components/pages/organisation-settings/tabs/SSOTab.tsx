import React from 'react'
import PlanBasedBanner from 'components/PlanBasedAccess'
import SamlTab from 'components/SamlTab'
import ScimSection from 'components/ScimSection'

type SSOTabProps = {
  organisationId: number
}

export const SSOTab = ({ organisationId }: SSOTabProps) => {
  return (
    <div className='d-flex flex-column gap-4 mt-4'>
      <PlanBasedBanner feature='SAML' theme='page'>
        <SamlTab organisationId={organisationId} />
      </PlanBasedBanner>
      <PlanBasedBanner feature='SCIM' theme='page'>
        <ScimSection organisationId={organisationId} />
      </PlanBasedBanner>
    </div>
  )
}
