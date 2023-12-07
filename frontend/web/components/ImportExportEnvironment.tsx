import React, { FC } from 'react'
import InfoMessage from './InfoMessage'
import Button from './base/forms/Button'

type ImportExportEnvironmentType = {
  environmentId: string
  projectId: string
}

const ImportExportEnvironment: FC<ImportExportEnvironmentType> = ({}) => {
  return (
    <>
      <InfoMessage>
        Import operations will overwrite existing feature flag values for the
        environment.
      </InfoMessage>

      <Button>Export Environment</Button>
    </>
  )
}

export default ImportExportEnvironment
