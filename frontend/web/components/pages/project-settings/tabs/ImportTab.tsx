import ImportPage from 'components/import-export/ImportPage'
import React from 'react'
import { useGetProjectQuery } from 'common/services/useProject'
import { ProjectSettingsTabProps } from 'components/pages/project-settings/shared/types'

export const ImportTab = ({
  environmentId,
  projectId,
}: ProjectSettingsTabProps) => {
  const { data: project } = useGetProjectQuery({ id: String(projectId) })

  if (!environmentId) {
    return null
  }

  return (
    <ImportPage
      environmentId={environmentId}
      projectId={projectId}
      projectName={project?.name || ''}
    />
  )
}
