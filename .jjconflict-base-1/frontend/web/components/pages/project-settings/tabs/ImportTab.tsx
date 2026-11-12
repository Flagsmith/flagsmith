import React from 'react'
import ImportPage from 'components/import-export/ImportPage'

type ImportTabProps = {
  projectName: string
  projectId: number
}

export const ImportTab = ({ projectId, projectName }: ImportTabProps) => {
  return <ImportPage projectId={projectId} projectName={projectName} />
}
