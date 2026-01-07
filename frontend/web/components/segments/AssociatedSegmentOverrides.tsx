import React, { FC, useEffect, useState } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import FeatureFilters, {
  parseFiltersFromUrlParams,
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
import ConnectedFeatureOverrideRow from 'components/ConnectedFeatureOverrideRow'

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
  const preselect = Utils.fromParam().flag
  const [filter, setFilter] = useState(
    parseFiltersFromUrlParams(Utils.fromParam()),
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

  // For regular segments, fetch all flags with segment overrides
  const {
    data: projectFlags,
    isFetching: projectFlagsFetching,
    isLoading: projectFlagsLoading,
  } = useGetProjectFlagsQuery(
    {
      ...getServerFilter(filter),
      environment: environment?.id || 0,
      project: `${projectId}`,
      segment: segmentId,
    },
    {
      skip: !projectId || !environment || !segmentId || !!segment?.feature,
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

  useEffect(() => {
    if (!environment && !!environments?.results?.[0]) {
      setEnvironment(environments.results[0])
    }
  }, [environment, environments])

  // Render the feature-specific segment view
  if (segment?.feature && environment) {
    return (
      <>
        <div>
          <PageTitle
            title={
              <div className='d-flex gap-4'>
                Associated Feature
                <div style={{ width: 200 }}>
                  <EnvironmentSelect
                    showAll={false}
                    value={environment?.api_key}
                    projectId={projectId}
                    onChange={(id) =>
                      setEnvironment(
                        environments?.results?.find((e) => e.api_key === id),
                      )
                    }
                  />
                </div>
              </div>
            }
          >
            This feature is specifically associated with the segment{' '}
            <strong className='text-primary'>{segment?.name}</strong>.
          </PageTitle>
        </div>
        <div className='panel panel-without-heading no-pad overflow-visible'>
          <ConnectedFeatureOverrideRow
            featureId={segment.feature}
            projectId={projectId}
            environmentId={environment.api_key}
            environmentIdNumeric={environment.id}
            segmentId={segmentId!}
            shouldPreselect={false}
            index={0}
            openInNewTab
          />
        </div>
      </>
    )
  }

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
                  value={environment?.api_key}
                  projectId={projectId}
                  onChange={(id) =>
                    setEnvironment(
                      environments?.results?.find((e) => e.api_key === id),
                    )
                  }
                />
              </div>
            </div>
          }
        >
          This will highlight any feature overridden by the segment{' '}
          <strong className='text-primary'>{segment?.name}</strong> in the
          chosen environment.
        </PageTitle>
      </div>
      {projectFlagsLoading ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        !!projectFlags && (
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
            isLoading={projectFlagsFetching}
            items={projectFlags.results}
            renderRow={(projectFlag, i) => {
              return (
                !!projectFlag &&
                !!environment && (
                  <FeatureOverrideRow
                    shouldPreselect={projectFlag.name === preselect}
                    environmentId={environment.api_key}
                    level='segment'
                    valueDataTest={`user-feature-value-${i}`}
                    projectFlag={projectFlag}
                    dataTest={`user-feature-${i}`}
                    overrideFeatureState={
                      projectFlag.segment_feature_state ||
                      projectFlag.environment_feature_state
                    }
                    environmentFeatureState={
                      projectFlag.environment_feature_state!
                    }
                    highlightSegmentId={segmentId}
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
        )
      )}
    </>
  )
}

export default AssociatedSegmentOverrides
