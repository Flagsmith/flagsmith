import React from 'react'
import PlanBasedBanner from 'components/PlanBasedAccess'
import SamlSection from 'components/SamlSection'
import ScimSection from 'components/ScimSection'

type SSOTabProps = {
  organisationId: number
}

export const SSOTab = ({ organisationId }: SSOTabProps) => {
  return (
    <>
      <PlanBasedBanner feature='SAML' theme='page' className='mt-4'>
        <SamlSection organisationId={organisationId} />
      </PlanBasedBanner>
      <PlanBasedBanner feature='SCIM' theme='page' className='mt-4'>
        <ScimSection organisationId={organisationId} />
      </PlanBasedBanner>
    </>
  )
}
