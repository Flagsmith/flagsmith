import InfoMessage from 'components/InfoMessage'
import MetadataPage from 'components/metadata/MetadataPage'
import React from 'react'

type CustomFieldsTabProps = {
  organisationId: number
  projectId: number
}

export const CustomFieldsTab = ({
  organisationId,
  projectId,
}: CustomFieldsTabProps) => {
  if (!organisationId) {
    return (
      <div className='mt-4'>
        <InfoMessage>Unable to load organisation settings</InfoMessage>
      </div>
    )
  }

  return (
    <div className='mt-4'>
      <MetadataPage
        organisationId={`${organisationId}`}
        projectId={`${projectId}`}
      />
    </div>
  )
}
