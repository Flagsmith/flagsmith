import React, { FC, useEffect, useRef, useState } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import Tooltip from 'components/Tooltip'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import TagFilter from 'components/tags/TagFilter'
import PanelSearch from 'components/PanelSearch'
import FeatureRow from 'components/feature-summary/FeatureRow'
import { ProjectFlag, TagStrategy } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import {
  useCreateFeatureExportMutation,
  useGetFeatureExportsQuery,
} from 'common/services/useFeatureExport'
import InfoMessage from 'components/InfoMessage'
import FeatureExportItem from './FeatureExportItem'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'

type FeatureExportType = {
  projectId: string
}

const FeatureExport: FC<FeatureExportType> = ({ projectId }) => {
  const [environment, setEnvironment] = useState<string>(
    ProjectStore.getEnvs()?.[0]?.api_key,
  )
  const [tags, setTags] = useState<(number | string)[]>([])
  const [search, setSearch] = useState()
  const [page, setPage] = useState(1)
  const [tagStrategy, setTagStrategy] = useState<TagStrategy>('UNION')

  const { getEnvironmentIdFromKey, isLoading: isLoadingEnvs } =
    useProjectEnvironments(parseInt(projectId))

  const environmentId = environment
    ? getEnvironmentIdFromKey(environment)
    : undefined

  const { data: featureListData, isFetching: isLoadingFeatures } =
    useGetFeatureListQuery(
      environmentId
        ? {
            environmentId: String(environmentId),
            page,
            projectId: parseInt(projectId),
            search: search || undefined,
            sort_direction: 'ASC',
            sort_field: 'name',
            tag_strategy: tagStrategy,
            tags: tags?.length ? tags.join(',') : undefined,
          }
        : ({} as any),
      { skip: !environmentId },
    )

  const projectFlags = featureListData?.results
  const environmentFlags = featureListData?.environmentStates
  const paging = featureListData?.pagination

  const [createFeatureExport, { isLoading: isCreating, isSuccess }] =
    useCreateFeatureExportMutation({})

  const { data: exports, refetch } = useGetFeatureExportsQuery({ projectId })
  const onSubmit = () => {
    const env = ProjectStore.getEnvironment(environment)
    createFeatureExport({
      environment_id: env.id,
      tag_ids: tags,
    }).then((res) => {
      if (res?.data) {
        toast('Your export is processing')
      } else {
        toast('Failed to export features')
      }
    })
  }
  const timerRef = useRef<NodeJS.Timer>()
  useEffect(() => {
    if (
      exports?.results.find(
        (featureExport) => featureExport.status === 'PROCESSING',
      )
    ) {
      timerRef.current = setTimeout(() => {
        refetch()
      }, 200)
    }
  }, [exports, refetch])
  return (
    <div className='mt-4'>
      <InfoMessage>
        This will export the project's features using the default values from a
        given environment.
      </InfoMessage>
      <div className='mb-2'>
        <Tooltip
          title={
            <>
              <strong>Environment</strong>
              <IonIcon icon={informationCircle} />
            </>
          }
        >
          {'Select the environment to use for the export.'}
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
        <Tooltip
          title={
            <>
              <strong>Filter Exported Features</strong>{' '}
              <IonIcon icon={informationCircle} />
            </>
          }
        >
          {
            'When tags are selected the export will contain all features that have at least one of the specified tags.'
          }
        </Tooltip>
      </div>
      <TagFilter
        hideTagStrategy
        showClearAll={!!tags?.length}
        onClearAll={() => setTags([])}
        projectId={`${projectId}`}
        value={tags}
        onChange={setTags}
      />
      {(() => {
        if (isLoadingEnvs || (isLoadingFeatures && !projectFlags)) {
          return (
            <div className='text-center'>
              <Loader />
            </div>
          )
        }
        return (
          <>
            <div className='mt-4 mb-2'>
              <strong>Features</strong>{' '}
            </div>
            <PanelSearch
              className='no-pad'
              id='features-list'
              renderSearchWithNoResults
              search={search}
              items={projectFlags}
              onChange={(e: InputEvent) => {
                setSearch(Utils.safeParseEventValue(e))
              }}
              isLoading={isLoadingFeatures}
              paging={paging}
              nextPage={() => setPage(page + 1)}
              renderRow={(projectFlag: ProjectFlag, i: number) => (
                <FeatureRow
                  readOnly
                  hideRemove
                  hideAudit
                  environmentFlags={environmentFlags}
                  environmentId={environment}
                  projectId={projectId}
                  index={i}
                  projectFlag={projectFlag}
                />
              )}
              prevPage={() => setPage(page - 1)}
              goToPage={setPage}
            />
            <div className='mt-4 text-right'>
              <Button
                disabled={isLoadingFeatures || !environment}
                onClick={onSubmit}
              >
                Export Features
              </Button>
            </div>
          </>
        )
      })()}

      {isCreating || !exports ? (
        <div className={'text-center'}>
          <Loader />
        </div>
      ) : (
        <PanelSearch
          noResultsText={(search) => (
            <Flex className='text-center'>No exports have been created</Flex>
          )}
          id='org-members-list'
          title='Exports'
          className='mt-4 no-pad overflow-visible'
          items={exports?.results}
          header={
            <Row className='table-header'>
              <Flex className='table-column px-3'>Export</Flex>
            </Row>
          }
          renderRow={(data) => <FeatureExportItem data={data} />}
        />
      )}
    </div>
  )
}

export default FeatureExport
