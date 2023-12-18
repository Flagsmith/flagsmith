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
  Res,
  User,
  UserGroupSummary,
} from 'common/types/responses'
import FeatureRow from 'components/FeatureRow'
import Button from 'components/base/forms/Button'
import { useCreateFlagsmithProjectImportMutation } from 'common/services/useFlagsmithProjectImport'
import ErrorMessage from 'components/ErrorMessage'
import InfoMessage from 'components/InfoMessage'
import WarningMessage from 'components/WarningMessage'
import FeatureListStore from 'common/stores/feature-list-store'
import SuccessMessage from 'components/SuccessMessage'

type FeatureExportType = {
  projectId: string
}

const FeatureExport: FC<FeatureExportType> = ({ projectId }) => {
  const [environment, setEnvironment] = useState<string>(
    ProjectStore.getEnvs()?.[0]?.api_key,
  )
  const [previewEnvironment, setPreviewEnvironment] = useState<string>(
    ProjectStore.getEnvs()?.[0]?.api_key,
  )
  const [tags, setTags] = useState<(number | string)[]>([])
  const [search, setSearch] = useState()
  const [page, setPage] = useState(0)
  const env = ProjectStore.getEnvironment(environment)
  const [file, setFile] = useState<File | null>(null)
  const [fileData, setFileData] = useState<FeatureImportItem[] | null>(null)
  const [currentProjectflags, setCurrentProjectflags] =
    useState<ProjectFlag[]>()
  const [currentFeatureStates, setCurrentFeatureStates] =
    useState<Record<number, FeatureState>>()

  useEffect(() => {
    const callback = () => {
      setCurrentProjectflags(FeatureListStore.getProjectFlags())
      setCurrentFeatureStates(FeatureListStore.getEnvironmentFlags())
    }
    FeatureListStore.on('change', callback)

    return () => {
      FeatureListStore.off('change', callback)
    }
  }, [])
  useEffect(() => {
    if (previewEnvironment) {
      AppActions.getFeatures(
        projectId,
        previewEnvironment,
        true,
        null,
        null,
        page,
        {
          search,
          tags: tags?.length ? tags : undefined,
        },
      )
    }
  }, [previewEnvironment, tags, search, projectId, page])

  const [createImport, { error, isLoading }] =
    useCreateFlagsmithProjectImportMutation({})

  const [success, setSuccess] = useState(false)

  const onSubmit = () => {
    if (env && file) {
      createImport({
        environment_id: env.id,
        file,
        strategy,
      }).then((res) => {
        if (res?.data) {
          setSuccess(true)
          setFile(null)
          setFileData(null)
        } else {
          toast('Failed to import flags')
        }
      })
    }
  }

  const [strategy, setStrategy] = useState<ImportStrategy>('SKIP')

  useEffect(() => {
    AppActions.getFeatures(projectId, environment, true, null, null, page, {
      search,
      tags: tags?.length ? tags : undefined,
    })
  }, [projectId, tags])
  const {
    featureStates,
    projectFlags,
  }: {
    projectFlags: ProjectFlag[] | null
    featureStates: FeatureState[] | null
  } = useMemo(() => {
    if (fileData) {
      const createdDate = new Date().toISOString()
      const existingFlags: ProjectFlag[] =
        !!fileData &&
        !!currentFeatureStates &&
        currentProjectflags?.map((projectFlag, i) => {
          const featureState = currentFeatureStates[projectFlag.id]
          const importItem = fileData.find((v) => v.name === projectFlag.name)
          let newValue = featureState.value
          let newEnabled = featureState.enabled

          // Overwrite destructive replaces existing feature values
          if (strategy === 'OVERWRITE_DESTRUCTIVE' && importItem) {
            // For the targeted environment it will use the imported feature values
            if (environment === previewEnvironment) {
              newEnabled = importItem.enabled
              newValue = importItem.value
            } else {
              // For every other environment the features are overwritten with the imported default enabled state and value
              newEnabled = importItem.default_enabled
              newValue = importItem.initial_value
            }
          }
          return {
            ...projectFlag,
            created_date: projectFlag.created_date,
            default_enabled: newEnabled,
            id: i,
            initial_value: newValue,
          }
        })

      const projectFlags = existingFlags.concat(
        fileData
          .filter((v) => {
            return !existingFlags.find((flag) => flag.name === v.name)
          })
          .map(function (importItem, i) {
            return {
              created_date: createdDate,
              default_enabled: importItem.enabled,
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
              type: importItem.multivariate?.length
                ? 'MULTIVARIATE'
                : 'STANDARD',
              uuid: `${i}`,
            }
          }),
      )

      const featureStates: FeatureState[] = projectFlags.map(
        (projectFlag, i) => {
          return {
            created_at: createdDate,
            enabled: projectFlag.default_enabled,
            environment: env!.id,
            feature: i,
            feature_state_value: projectFlag.initial_value,
            id: i,
            multivariate_feature_state_values: projectFlag.multivariate_options,
            uuid: `${i}`,
          }
        },
      )
      return { featureStates, projectFlags }
    }
    return { featureStates: null, projectFlags: null }
  }, [fileData, currentFeatureStates, currentProjectflags, strategy, env])
  return (
    <div className='mt-4'>
      {success ? (
        <SuccessMessage>
          Your import is processing, it may take several minutes for the import
          to complete.
        </SuccessMessage>
      ) : (
        <InfoMessage>
          The selected environment will inherit the imported environment's
          values where as all other environments will inherit the default
          values.
        </InfoMessage>
      )}

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
            onChange={(e) => {
              setEnvironment(e)
              setPreviewEnvironment(e)
            }}
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
              'Overwrite Destructive (existing features will be overwritten).'
            }
            onChange={() => setStrategy('OVERWRITE_DESTRUCTIVE')}
            checked={strategy === 'OVERWRITE_DESTRUCTIVE'}
          />
        </div>
      </div>
      {strategy === 'OVERWRITE_DESTRUCTIVE' && (
        <WarningMessage
          warningMessage={
            'Using overwrite destructive may affect ALL environments. Features in environments other than the one being imported to will receive the defaults defined in the import. Use with caution.'
          }
        />
      )}
      <div className='my-2'>
        <strong>Import File</strong>
      </div>
      <JSONUpload
        value={file}
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
          <div className='my-2 col-6 col-lg-4'>
            <EnvironmentSelect
              projectId={projectId}
              onChange={(e) => {
                setPreviewEnvironment(e)
              }}
              value={previewEnvironment}
            />
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
                environmentId={previewEnvironment}
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
