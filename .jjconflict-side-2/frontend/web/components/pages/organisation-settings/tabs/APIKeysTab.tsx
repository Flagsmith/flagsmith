import React from 'react'
import ManagementAPIKeys from 'components/ManagementAPIKeys'
import Utils from 'common/utils/utils'
import TrustRelationships from './trust-relationships'

type APIKeysTabProps = {
  organisationId: number
}

export const APIKeysTab = ({ organisationId }: APIKeysTabProps) => {
  return (
    <>
      <ManagementAPIKeys organisationId={organisationId} />
      {Utils.getFlagsmithHasFeature('trust_relationships') && (
        <TrustRelationships organisationId={organisationId} />
      )}
    </>
  )
}
