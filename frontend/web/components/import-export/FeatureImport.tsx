import React, { FC, useEffect, useState } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import Tooltip from 'components/Tooltip'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import AppActions from 'common/dispatcher/app-actions'
import ProjectStore from 'common/stores/project-store'
import {
  useCreateFeatureExportMutation,
  useGetFeatureExportsQuery,
} from 'common/services/useFeatureExport'
import Radio from 'components/base/forms/Radio'
import { ImportStrategy } from 'common/types/requests'
import JSONUpload from 'components/JSONUpload'

type FeatureExportType = {
  projectId: string
}

const FeatureExport: FC<FeatureExportType> = ({ projectId }) => {
  const [environment, setEnvironment] = useState<string>(
    ProjectStore.getEnvs()?.[0]?.api_key,
  )
  const [tags, setTags] = useState<(number | string)[]>([])
  const [search, setSearch] = useState()
  const [page, setPage] = useState(0)

  useEffect(() => {
    if (environment) {
      AppActions.getFeatures(projectId, environment, true, null, null, page, {
        search,
        tags: tags?.length ? tags : undefined,
      })
    }
  }, [environment, tags, search, projectId, page])
  const [createFeatureExport, { isLoading: isCreating, isSuccess }] =
    useCreateFeatureExportMutation({})

  const { data: exports } = useGetFeatureExportsQuery({ projectId })
  const onSubmit = () => {
    const env = ProjectStore.getEnvironment(environment)
    createFeatureExport({
      environment_id: env.id,
      tag_ids: tags,
    })
  }

  const [strategy, setStrategy] = useState<ImportStrategy>('SKIP')

  return (
    <div className='mt-4'>
      <div className='mb-2'>
        <Tooltip
          title={
            <>
              <strong>Environment</strong>
              <IonIcon icon={informationCircle} />
            </>
          }
        >
          {'Determines the environment to import feature values to.'}
        </Tooltip>
      </div>
      <div className='row'>
        <div className='my-2 col-6 col-lg-4'>
          <EnvironmentSelect
            projectId={projectId}
            onChange={setEnvironment}
            value={environment}
          />
        </div>
      </div>
      <div className='my-2'>
        <strong>Merge Strategy</strong>
        <div className='mt-2'>
          <Radio
            label={'Skip  (existing features will be ignored)'}
            onChange={() => setStrategy('SKIP')}
            checked={strategy === 'SKIP'}
          />
        </div>
        <div>
          <Radio
            label={
              'Overwrite Destructive (existing features will be overwritten)'
            }
            onChange={() => setStrategy('OVERWRITE_DESTRUCTIVE')}
            checked={strategy === 'OVERWRITE_DESTRUCTIVE'}
          />
        </div>
      </div>
      <div className='my-2'>
        <strong>Import File</strong>
      </div>
      <JSONUpload />
    </div>
  )
}

export default FeatureExport
