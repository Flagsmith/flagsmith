import React, { FC, useState } from 'react'
import EnvironmentSelect from './EnvironmentSelect'
import Button from './base/forms/Button'
import { Env } from '@stencil/core'
import Tooltip from './Tooltip'

type FeatureExportType = {
  projectId: string
}

type FeatureExportInnerType = {
  projectId: string
}

const FeatureExportInner: FC<FeatureExportInnerType> = ({ projectId }) => {
  const [environment, setEnvironment] = useState()

  return (
    <div className='px-4'>
      <Tooltip title={<strong>Environment</strong>}>
        {
          'Selecting an environment will determine the feature defaults used when importing to a project'
        }
      </Tooltip>

      <EnvironmentSelect projectId={projectId} onChange={environment} />
    </div>
  )
}

const FeatureExport: FC<FeatureExportType> = ({ projectId }) => {
  const [environment, setEnvironment] = useState<string>()

  return (
    <>
      <Button
        onClick={() => {
          openModal(
            'Export Features',
            <FeatureExportInner projectId={projectId} />,
            'side-modal',
          )
        }}
      >
        Export Features
      </Button>
    </>
  )
}

export default FeatureExport
