import React, { FC, useEffect, useState } from 'react'
import { useGetSegmentFeatureStatesQuery } from 'common/services/useFeatureState'
import EnvironmentSelect from 'components/EnvironmentSelect'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import FeatureFilters, {
  getFiltersFromURLParams,
  getServerFilter,
  getURLParamsFromFilters,
} from 'components/feature-page/FeatureFilters'
import Utils from 'common/utils/utils'
import PanelSearch from 'components/PanelSearch'
import JSONReference from 'components/JSONReference'
import AccountStore from 'common/stores/account-store'
import FeatureListStore from 'common/stores/feature-list-store'
import FeatureOverrideRow from 'components/feature-override/FeatureOverrideRow'
import { useHistory } from 'react-router-dom'
import { Environment } from 'common/types/responses'
import { useGetSegmentQuery } from 'common/services/useSegment'
import PageTitle from 'components/PageTitle'

type AssociatedSegmentOverridesType = {
  projectId: number
  segmentId: number | undefined
}

const AssociatedSegmentOverrides: FC<AssociatedSegmentOverridesType> = ({
  projectId,
  segmentId,
}) => {
  const history = useHistory()
  const [environment, setEnvironment] = useState<Environment>()
  const [filter, setFilter] = useState(
    getFiltersFromURLParams(Utils.fromParam()),
  )
  const { data: segment } = useGetSegmentQuery(
    {
      id: segmentId!,
      projectId: projectId!,
    },
    {
      skip: !projectId || !segmentId,
    },
  )
  const { data: projectFlags, isLoading: projectFlagsLoading } =
    useGetProjectFlagsQuery(
      {
        ...getServerFilter(filter),
        project: `${projectId}`,
      },
      {
        skip: !projectId,
      },
    )

  const { data: environments } = useGetEnvironmentsQuery(
    {
      projectId: `${projectId}`,
    },
    {
      skip: !projectId,
    },
  )

  const { data: featureStates } = useGetSegmentFeatureStatesQuery(
    {
      environmentId: (environment || { id: 1 }).id,
      features: projectFlags?.results?.map((v) => v.id),
      segmentId: segmentId!,
    },
    { skip: !segmentId || !environment?.id },
  )

  const isLoading = !projectFlags || !featureStates || !environment

  useEffect(() => {
    if (!environment && !!environments?.results?.[0]) {
      setEnvironment(environments.results[0])
    }
  }, [environment, environments])
  return (
    <>
      <div>
        <PageTitle
          title={
            <div className='d-flex gap-4'>
              Associated Features
              <div style={{ width: 200 }}>
                <EnvironmentSelect
                  showAll={false}
                  value={environment?.id}
                  projectId={projectId}
                  onChange={(id, environment) => setEnvironment(environment)}
                  idField={'id'}
                />
              </div>
            </div>
          }
        >
          This will highlight any feature overriden by the segment{' '}
          <strong className='text-primary'>{segment?.name}</strong> in the
          chosen environment.
        </PageTitle>
      </div>
      {isLoading ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <PanelSearch
          id='user-features-list'
          className='no-pad overflow-visible'
          itemHeight={70}
          renderFooter={() => (
            <>
              <JSONReference
                showNamesButton
                className='mt-4 mx-2'
                title={'Features'}
                json={projectFlags}
              />
              <JSONReference
                className='mx-2'
                title={'Feature States'}
                json={featureStates}
              />
            </>
          )}
          header={
            <FeatureFilters
              value={filter}
              projectId={projectId!}
              orgId={AccountStore.getOrganisation()?.id}
              isLoading={projectFlagsLoading}
              onChange={(next) => {
                FeatureListStore.isLoading = true
                history.replace(
                  `${document.location.pathname}?${Utils.toParam(
                    getURLParamsFromFilters(next),
                  )}`,
                )
                setFilter(next)
              }}
            />
          }
          isLoading={projectFlagsLoading}
          items={projectFlags.results}
          renderRow={(projectFlag, i) => {
            const overrideFeatureState = featureStates.results.find(
              (v) => v.featureState.feature === projectFlag.id,
            )
            return (
              !!projectFlag &&
              !!overrideFeatureState && (
                <FeatureOverrideRow
                  environmentId={environment.api_key}
                  level='segment'
                  valueDataTest={`user-feature-value-${i}`}
                  projectFlag={projectFlag}
                  dataTest={`user-feature-${i}`}
                  overrideFeatureState={overrideFeatureState.segmentOverride}
                  environmentFeatureState={overrideFeatureState.featureState}
                />
              )
            )
          }}
          renderSearchWithNoResults
          paging={projectFlags}
          nextPage={() =>
            setFilter({
              ...filter,
              page: filter.page + 1,
            })
          }
          prevPage={() =>
            setFilter({
              ...filter,
              page: filter.page - 1,
            })
          }
          goToPage={(page) => {
            setFilter({
              ...filter,
              page,
            })
          }}
        />
      )}
    </>
  )
}

export default AssociatedSegmentOverrides
