import ImportPage from 'components/import-export/ImportPage'
import InfoMessage from 'components/InfoMessage'
import React from 'react'
import { useGetProjectQuery } from 'common/services/useProject'

type ImportTabProps = {
  projectId: number
  environmentId?: string
}

export const ImportTab = ({ environmentId, projectId }: ImportTabProps) => {
  const { data: project, isLoading } = useGetProjectQuery({
    id: String(projectId),
  })

  if (isLoading) {
    return (
      <div className='text-center mt-4'>
        <Loader />
      </div>
    )
  }

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
      projectName={project?.name || ''}
    />
  )
}
