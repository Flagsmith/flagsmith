import React, { FC, useMemo, useState } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import Tooltip from 'components/Tooltip'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import ProjectStore from 'common/stores/project-store'
import Radio from 'components/base/forms/Radio'
import { ImportStrategy } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import JSONUpload from 'components/JSONUpload'
import PanelSearch from 'components/PanelSearch'
import {
  FeatureImportItem,
  FeatureState,
  TagStrategy,
} from 'common/types/responses'
import FeatureRow from 'components/feature-summary/FeatureRow'
import Button from 'components/base/forms/Button'
import { useCreateFlagsmithProjectImportMutation } from 'common/services/useFlagsmithProjectImport'
import ErrorMessage from 'components/ErrorMessage'
import InfoMessage from 'components/InfoMessage'
import WarningMessage from 'components/WarningMessage'
import SuccessMessage from 'components/messages/SuccessMessage'
import TableSearchFilter from 'components/tables/TableSearchFilter'
import Utils from 'common/utils/utils'
import TableTagFilter from 'components/tables/TableTagFilter'
import TableFilterOptions from 'components/tables/TableFilterOptions'
import { getViewMode, setViewMode } from 'common/useViewMode'
import TableSortFilter, { SortValue } from 'components/tables/TableSortFilter'
import { useGetFeatureImportsQuery } from 'common/services/useFeatureImport'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'

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
  const { data: featureImports, refetch } = useGetFeatureImportsQuery({
    projectId,
  })
  const [tags, setTags] = useState<(number | string)[]>([])
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const env = ProjectStore.getEnvironment(environment)
  const [file, setFile] = useState<File | null>(null)
  const [fileData, setFileData] = useState<FeatureImportItem[] | null>(null)

  const { getEnvironmentIdFromKey, isLoading: _isLoadingEnvs } =
    useProjectEnvironments(parseInt(projectId))

  const previewEnvId = previewEnvironment
    ? getEnvironmentIdFromKey(previewEnvironment)
    : undefined

  const baseEnvId = environment
    ? getEnvironmentIdFromKey(environment)
    : undefined

  const [showArchived, setShowArchived] = useState(false)

  const [tagStrategy, setTagStrategy] = useState<TagStrategy>('UNION')
  const [sort, setSort] = useState<SortValue>({
    label: 'Name',
    sortBy: 'name',
    sortOrder: SortOrder.ASC,
  })

  // Fetch features for the preview environment (with filters/search)
  const { isFetching: isLoadingPreview } = useGetFeatureListQuery(
    previewEnvId
      ? {
          environmentId: String(previewEnvId),
          is_archived: showArchived,
          page,
          projectId: parseInt(projectId),
          search: search || undefined,
          sort_direction: sort.sortOrder,
          sort_field: sort.sortBy,
          tag_strategy: tagStrategy,
          tags: tags?.length ? tags.join(',') : undefined,
        }
      : ({} as any),
    { skip: !previewEnvId },
  )

  // Fetch base environment features for comparison with import data
  const { data: baseFeatureData } = useGetFeatureListQuery(
    baseEnvId
      ? {
          environmentId: String(baseEnvId),
          page: 1,
          projectId: parseInt(projectId),
          search: search || undefined,
          sort_direction: 'ASC',
          sort_field: 'name',
          tags: tags?.length ? tags.join(',') : undefined,
        }
      : ({} as any),
    { skip: !baseEnvId },
  )

  const currentProjectflags = baseFeatureData?.results
  const currentFeatureStates = baseFeatureData?.environmentStates

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
          refetch()
        } else {
          toast('Failed to import flags')
        }
      })
    }
  }

  const [strategy, setStrategy] = useState<ImportStrategy>('SKIP')

  const { featureStates, projectFlags } = useMemo(() => {
    if (fileData) {
      const createdDate = new Date().toISOString()
      const existingFlags =
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

      const fileFlags = fileData
        .filter((v) => {
          return !existingFlags.find((flag) => flag.name === v.name)
        })
        .map(function (importItem, i) {
          return {
            created_date: createdDate,
            default_enabled: importItem.enabled,
            group_owners: [],
            id: i,
            initial_value: importItem.value,
            isNew: true,
            is_archived: false,
            is_server_key_only: importItem.is_server_key_only,
            multivariate_options: importItem.multivariate,
            name: importItem.name,
            num_identity_overrides: 0,
            num_segment_overrides: 0,
            owners: [],
            project: ProjectStore.model!.id,
            tags: [],
            type: importItem.multivariate?.length ? 'MULTIVARIATE' : 'STANDARD',
            uuid: `${i}`,
          }
        })
      const projectFlags = existingFlags.concat(fileFlags)

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
  }, [
    fileData,
    currentFeatureStates,
    currentProjectflags,
    strategy,
    env,
    environment,
    previewEnvironment,
  ])

  const filteredProjectFlags = useMemo(() => {
    return projectFlags?.filter((projectFlag) => {
      if (!projectFlag.isNew) {
        return true
      }
      // Filter out any tags/search criteria
      if (
        !!search &&
        !projectFlag?.name.toLowerCase()?.includes(search.toLowerCase())
      ) {
        return false
      }
      if (showArchived) {
        return false
      }
      if (
        tagStrategy === 'INTERSECTION' &&
        tags.length &&
        !(tags.length === 1 && tags[0] === '')
      ) {
        return false
      }
      return true
    })
  }, [projectFlags, search, tags, tagStrategy, showArchived])

  const processingImport = useMemo(() => {
    return featureImports?.results?.find(
      (featureImport) => featureImport.status === 'PROCESSING',
    )
  }, [featureImports])
  if (processingImport) {
    return (
      <div className='mt-4'>
        <InfoMessage>
          Your import is processing, it may take several minutes for the import
          to complete.
        </InfoMessage>
      </div>
    )
  }
  return (
    <div className='mt-4'>
      {success ? (
        <SuccessMessage>Your import has been processed.</SuccessMessage>
      ) : (
        <InfoMessage>
          The selected environment will inherit the imported environment's
          values. All other environments will inherit the default values.
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
            'Using overwrite destructive may affect ALL environments. All other environments will be set to the values defined when the feature was initially created. Use with caution.'
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
      {!!filteredProjectFlags && (
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
            className='no-pad overflow-visible'
            id='features-list'
            renderSearchWithNoResults
            search={search}
            items={filteredProjectFlags?.filter((v) => {
              return search ? v.name.toLowerCase().includes(search) : true
            })}
            header={
              <Row className='table-header'>
                <div className='table-column flex-row flex-fill'>
                  <TableSearchFilter
                    onChange={(e) => {
                      setSearch(Utils.safeParseEventValue(e))
                    }}
                    value={search}
                  />
                  <Row className='flex-fill justify-content-end'>
                    <TableTagFilter
                      isLoading={isLoadingPreview}
                      projectId={projectId}
                      className='me-4'
                      tagStrategy={tagStrategy}
                      onChangeStrategy={setTagStrategy}
                      value={tags}
                      onToggleArchived={() => {
                        setShowArchived(!showArchived)
                      }}
                      showArchived={showArchived}
                      onChange={(tags) => {
                        if (tags.includes('') && tags.length > 1) {
                          if (!tags.includes('')) {
                            setTags([''])
                          } else {
                            setTags(tags.filter((v) => !!v))
                          }
                        } else {
                          setTags(tags)
                        }
                      }}
                    />
                    <TableFilterOptions
                      title={'View'}
                      className={'me-4'}
                      value={getViewMode()}
                      onChange={setViewMode}
                      options={[
                        {
                          label: 'Default',
                          value: 'default',
                        },
                        {
                          label: 'Compact',
                          value: 'compact',
                        },
                      ]}
                    />
                    <TableSortFilter
                      isLoading={isLoadingPreview}
                      value={sort}
                      options={[
                        {
                          label: 'Name',
                          value: 'name',
                        },
                        {
                          label: 'Created Date',
                          value: 'created_date',
                        },
                      ]}
                      onChange={setSort}
                    />
                  </Row>
                </div>
              </Row>
            }
            renderRow={(projectFlag, i) => (
              <FeatureRow
                hideAudit
                disableControls
                environmentFlags={featureStates ?? undefined}
                environmentId={previewEnvironment}
                projectId={projectId}
                index={projectFlag?.id || i}
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
