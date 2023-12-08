import React, { FC, useEffect, useState } from 'react'
import EnvironmentSelect from './EnvironmentSelect'
import Tooltip from './Tooltip'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import TagFilter from './tags/TagFilter'
import PanelSearch from './PanelSearch'
import FeatureListStore from 'common/stores/feature-list-store'
import FeatureListProvider from 'common/providers/FeatureListProvider'
import AppActions from 'common/dispatcher/app-actions'
import FeatureRow from './FeatureRow'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'
import {
  useCreateFeatureExportMutation,
  useGetFeatureExportQuery,
} from 'common/services/useFeatureExport'
import InfoMessage from './InfoMessage'

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
  const [isLoading, setIsLoading] = useState()

  const onSubmit = () => {
    const env = ProjectStore.getEnvironment(environment)
    createFeatureExport({
      environment_id: env.id,
      tag_ids: tags,
    })
  }
  return (
    <div className='mt-4'>
      <InfoMessage>
        This will export the project's features using the default values from a
        given environment.
      </InfoMessage>
      <div className='d-flex flex-column'>
        <div className='d-flex flex-column flex-fill'>
          <div className='mb-2'>
            <Tooltip
              title={
                <>
                  <strong>Environment</strong>
                  <IonIcon icon={informationCircle} />
                </>
              }
            >
              {
                'Selecting an environment will determine the feature defaults used when importing to a project'
              }
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
                  <strong>Filter</strong> <IonIcon icon={informationCircle} />
                </>
              }
            >
              {
                'If any tags are selected then the exported file will only include features that are tagged.'
              }
            </Tooltip>
          </div>
          <TagFilter
            showClearAll={!!tags?.length}
            onClearAll={() => setTags([])}
            projectId={`${projectId}`}
            value={tags}
            onChange={setTags}
          />
          <FeatureListProvider>
            {({
              environmentFlags,
              projectFlags,
            }: {
              environmentFlags?: FeatureState[]
              projectFlags: ProjectFlag[]
            }) => {
              const isLoading = !FeatureListStore.hasLoaded

              if (isLoading) {
                return (
                  <div className='text-center'>
                    <Loader />
                  </div>
                )
              }
              return (
                <>
                  <div className='my-2'>
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
                    isLoading={FeatureListStore.isLoading}
                    paging={FeatureListStore.paging}
                    nextPage={() => setPage(page + 1)}
                    renderRow={(projectFlag: ProjectFlag, i: number) => (
                      <FeatureRow
                        readOnly
                        hideRemove
                        hideAudit
                        descriptionInTooltip
                        hideActions
                        size='sm'
                        environmentFlags={environmentFlags}
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
                  <div className='mt-4 text-right'>
                    <Button
                      disabled={isLoading || !environment}
                      onClick={onSubmit}
                    >
                      Export Features
                    </Button>
                  </div>
                </>
              )
            }}
          </FeatureListProvider>
        </div>
      </div>
    </div>
  )
}

export default FeatureExport
