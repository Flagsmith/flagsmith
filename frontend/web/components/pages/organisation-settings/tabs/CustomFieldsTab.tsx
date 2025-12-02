import React from 'react'
import MetadataPage from 'components/metadata/MetadataPage'

type CustomFieldsTabProps = {
  organisationId: number
}

export const CustomFieldsTab = ({ organisationId }: CustomFieldsTabProps) => {
  return <MetadataPage organisationId={organisationId} />
}
