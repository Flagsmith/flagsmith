import React from 'react'
import PlanBasedBanner from 'components/PlanBasedAccess'
import SamlTab from 'components/SamlTab'
import ScimSection from 'components/ScimSection'

type SSOTabProps = {
  organisationId: number
}

export const SSOTab = ({ organisationId }: SSOTabProps) => {
  return (
    <>
      <PlanBasedBanner feature='SAML' theme='page' className='mt-4'>
        <SamlTab organisationId={organisationId} />
      </PlanBasedBanner>
      <PlanBasedBanner feature='SCIM' theme='page' className='mt-4'>
        <ScimSection organisationId={organisationId} />
      </PlanBasedBanner>
    </>
  )
}
