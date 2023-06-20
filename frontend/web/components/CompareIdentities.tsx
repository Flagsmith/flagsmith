import React, { FC, useCallback, useEffect, useState } from 'react'
import IdentitySelect, { IdentitySelectType } from './IdentitySelect'
import Utils from 'common/utils/utils'
import EnvironmentSelect from './EnvironmentSelect'
const AppActions = require('common/dispatcher/app-actions')
import IdentityProvider from 'common/providers/IdentityProvider'
import PanelSearch from './PanelSearch'
import TagFilter from './tags/TagFilter'
import { useGetTagsQuery } from 'common/services/useTag'
import FeatureListStore from 'common/stores/feature-list-store'
import Tag from './tags/Tag'

type CompareIdentitiesType = {
  projectId: string
  environmentId: string
}
const selectWidth = 300

const CompareIdentities: FC<CompareIdentitiesType> = ({
  environmentId: _environmentId,
  projectId,
}) => {
  const [leftId, setLeftId] = useState<IdentitySelectType['value']>()
  const [rightId, setRightId] = useState<IdentitySelectType['value']>()
  const [environmentId, setEnvironmentId] = useState(_environmentId)

  const [filter, setFilter] = useState<{
    is_archived: boolean
    tags: (number | string)[]
  }>({
    is_archived: false,
    tags: [],
  })

  const [search, setSearch] = useState('')
  const [sort, setSort] = useState()
  const { data: tags } = useGetTagsQuery({ projectId })
  const [lastUpdated, setLastUpdated] = useState(0) //todo: this has to exist until we remove FeatureListStore

  const onFeatureListStoreChange = useCallback(() => {
    setLastUpdated(Date.now())
  }, [])
  useEffect(() => {
    FeatureListStore.on('changed')
  }, [])

  useEffect(() => {
    AppActions.getFeatures(
      projectId,
      environmentId,
      true,
      search,
      sort,
      0,
      filter,
    )
  }, [environmentId])

  const isReady = !!rightId && leftId
  useEffect(() => {
    setLeftId(null)
    setRightId(null)
  }, [environmentId])

  const isEdge = Utils.getIsEdge()
  return (
    <div>
      <h3>Compare Identities</h3>
      <p>Compare feature states between 2 identities</p>
      <div className='mb-2' style={{ width: selectWidth }}>
        <EnvironmentSelect
          value={environmentId}
          projectId={projectId}
          onChange={setEnvironmentId}
        />
      </div>
      <Row>
        <div className='mr-2' style={{ width: selectWidth }}>
          <IdentitySelect
            value={leftId}
            isEdge={isEdge}
            ignoreIds={[`${rightId?.value}`]}
            onChange={setLeftId}
            environmentId={environmentId}
          />
        </div>
        <div>
          <span className='icon ios ion-md-arrow-back mx-2' />
        </div>
        <div className='mr-2' style={{ width: selectWidth }}>
          <IdentitySelect
            value={rightId}
            ignoreIds={[`${leftId?.value}`]}
            isEdge={isEdge}
            onChange={setRightId}
            environmentId={environmentId}
          />
        </div>
      </Row>
      {isReady && (
        <>
          <IdentityProvider>
            {({
              environmentFlags,
              identity,
              identityFlags,
              isLoading,
              projectFlags,
              traits,
            }) => (
              <PanelSearch
                id='user-features-list'
                className='no-pad'
                itemHeight={70}
                icon='ion-ios-rocket'
                title='Features'
                header={
                  <div className='pb-2'>
                    <TagFilter
                      showUntagged
                      showClearAll={
                        !!filter.tags?.length || !!filter.is_archived
                      }
                      onClearAll={() =>
                        setFilter({ is_archived: false, tags: [] })
                      }
                      projectId={`${projectId}`}
                      value={filter.tags}
                      onChange={(tags) => {
                        FeatureListStore.isLoading = true
                        if (tags?.includes('') && tags?.length > 1) {
                          if (!filter.tags.includes('')) {
                            setFilter({
                              ...filter,
                              tags: [''],
                            })
                          } else {
                            setFilter({
                              ...filter,
                              tags: tags?.filter((v) => !!v),
                            })
                          }
                        } else {
                          setFilter({
                            ...filter,
                            tags,
                          })
                        }
                      }}
                    >
                      <Tag
                        selected={filter.is_archived}
                        onClick={() => {
                          FeatureListStore.isLoading = true
                          setFilter({
                            ...filter,
                            is_archived: !filter.is_archived,
                          })
                        }}
                        className='px-2 py-2 ml-2 mr-2'
                        tag={{ label: 'Archived' }}
                      />
                    </TagFilter>
                  </div>
                }
                isLoading={FeatureListStore.isLoading}
                onSortChange={setSort}
                items={projectFlags}
                sorting={[
                  {
                    default: true,
                    label: 'Name',
                    order: 'asc',
                    value: 'name',
                  },
                  {
                    label: 'Created Date',
                    order: 'asc',
                    value: 'created_date',
                  },
                ]}
                renderRow={({ id, name }, i) => <div>Row</div>}
              />
            )}
          </IdentityProvider>
        </>
      )}
    </div>
  )
}

export default CompareIdentities
