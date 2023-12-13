import React, { FC, useEffect, useMemo, useState } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import Tooltip from 'components/Tooltip'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import AppActions from 'common/dispatcher/app-actions'
import ProjectStore from 'common/stores/project-store'
import { useGetFeatureExportsQuery } from 'common/services/useFeatureExport'
import Radio from 'components/base/forms/Radio'
import { ImportStrategy } from 'common/types/requests'
import JSONUpload from 'components/JSONUpload'
import PanelSearch from 'components/PanelSearch'
import {
  FeatureImportItem,
  FeatureState,
  MultivariateFeatureStateValue,
  MultivariateOption,
  ProjectFlag,
  User,
  UserGroupSummary,
} from 'common/types/responses'
import FeatureRow from 'components/FeatureRow'
import Button from 'components/base/forms/Button'
import { useCreateFlagsmithProjectImportMutation } from 'common/services/useFlagsmithProjectImport'
import ErrorMessage from 'components/ErrorMessage'

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
  const env = ProjectStore.getEnvironment(environment)
  const [file, setFile] = useState<File | null>(null)
  const [fileData, setFileData] = useState<FeatureImportItem[] | null>(null)

  useEffect(() => {
    if (environment) {
      AppActions.getFeatures(projectId, environment, true, null, null, page, {
        search,
        tags: tags?.length ? tags : undefined,
      })
    }
  }, [environment, tags, search, projectId, page])

  const [createImport, { error, isLoading }] =
    useCreateFlagsmithProjectImportMutation({})
  const { data: exports } = useGetFeatureExportsQuery({ projectId })

  const onSubmit = () => {
    if (env && file) {
      createImport({
        environment_id: env.id,
        file,
        strategy,
      }).then((res) => {
        if (res?.data) {
          toast('Your import is processing')
        } else {
          toast('Failed to import flags')
        }
      })
    }
  }

  const [strategy, setStrategy] = useState<ImportStrategy>('SKIP')

  const {
    featureStates,
    projectFlags,
  }: {
    projectFlags: ProjectFlag[] | null
    featureStates: FeatureState[] | null
  } = useMemo(() => {
    if (fileData) {
      const createdDate = new Date().toISOString()
      const projectFlags: ProjectFlag[] = fileData.map((importItem, i) => {
        return {
          created_date: createdDate,
          default_enabled: importItem.enabled,
          description: null,
          id: i,
          initial_value: importItem.value,
          is_archived: false,
          is_server_key_only: importItem.is_server_key_only,
          multivariate_options: importItem.multivariate,
          name: importItem.name,
          num_identity_overrides: 0,
          num_segment_overrides: 0,
          owner_groups: [],
          owners: [],
          project: ProjectStore.model!.id,
          tags: [],
          type: 'STANDARD',
          uuid: `${i}`,
        }
      })
      const featureStates: FeatureState[] = fileData.map((importItem, i) => {
        return {
          created_at: createdDate,
          enabled: importItem.enabled,
          environment: env!.id,
          feature: i,
          feature_state_value: importItem.value,
          id: i,
          multivariate_feature_state_values: importItem.multivariate,
          uuid: `${i}`,
        }
      })
      return { featureStates, projectFlags }
    }
    return { featureStates: null, projectFlags: null }
  }, [fileData, env])
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
      <JSONUpload
        onChange={(file, data) => {
          setFile(file)
          setFileData(data)
        }}
      />
      {!!projectFlags && (
        <>
          <div className='my-2'>
            <strong>Preview</strong>
          </div>
          <PanelSearch
            className='no-pad'
            id='features-list'
            renderSearchWithNoResults
            search={search}
            items={projectFlags}
            renderRow={(projectFlag: ProjectFlag, i: number) => (
              <FeatureRow
                hideAudit
                disableControls
                size='sm'
                environmentFlags={featureStates}
                projectFlags={projectFlags}
                environmentId={environment}
                projectId={projectId}
                index={i}
                projectFlag={projectFlag}
              />
            )}
            prevPage={() => setPage(page - 1)}
            goToPage={setPage}
          />
          <ErrorMessage>{error}</ErrorMessage>
          <div className='mt-4 text-right'>
            <Button disabled={isLoading} onClick={onSubmit}>
              Import Features
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

export default FeatureExport
