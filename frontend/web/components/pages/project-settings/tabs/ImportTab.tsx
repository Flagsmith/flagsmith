import ImportPage from 'components/import-export/ImportPage'
import InfoMessage from 'components/InfoMessage'
import React from 'react'

type ImportTabProps = {
  projectName: string
  projectId: string
  environmentId?: string
}

export const ImportTab = ({
  environmentId,
  projectId,
  projectName,
}: ImportTabProps) => {
  if (!environmentId) {
    return (
      <div className='mt-4'>
        <InfoMessage>
          Please select an environment to import features
        </InfoMessage>
      </div>
    )
  }

  return (
    <ImportPage
      environmentId={environmentId}
      projectId={projectId}
      projectName={projectName}
    />
  )
}
