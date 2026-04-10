import React, { FC, useMemo, useState } from 'react'
import InfoMessage from 'components/InfoMessage'
import EnvironmentTagSelect from 'components/EnvironmentTagSelect'
import BarChart from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import {
  useGetEnvironmentAnalyticsQuery,
  useGetFeatureAnalyticsQuery,
} from 'common/services/useFeatureAnalytics'
import { Res } from 'common/types/responses'
import {
  aggregateByLabels,
  buildEnvColorMap,
  hasLabelledData,
} from './analyticsUtils'

type FlagAnalyticsType = {
  projectId: string
  featureId: string
  defaultEnvironmentIds: string[]
}

const FlagAnalytics: FC<FlagAnalyticsType> = ({
  defaultEnvironmentIds,
  featureId,
  projectId,
}) => {
  const [environmentIds, setEnvironmentIds] = useState(defaultEnvironmentIds)
  const [selectedLabels, setSelectedLabels] = useState<string[]>([])

  const { data, isLoading } = useGetFeatureAnalyticsQuery(
    {
      environment_ids: environmentIds,
      feature_id: featureId,
      period: 30,
      project_id: projectId,
    },
    {
      skip: !environmentIds?.length || !featureId || !projectId,
    },
  )

  const rawResponses = environmentIds.map((envId) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data: envData } = useGetEnvironmentAnalyticsQuery(
      {
        environment_id: envId,
        feature_id: featureId,
        period: 30,
        project_id: projectId,
      },
      {
        skip: !envId || !featureId || !projectId,
      },
    )
    return envData
  })

  const allRawData = useMemo(
    (): Res['environmentAnalytics'] => rawResponses.filter(Boolean).flat(),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(rawResponses)],
  )

  const isLabelled = hasLabelledData(allRawData)

  const {
    chartData: labelledChartData,
    colorMap,
    labelValues,
  } = useMemo(
    () =>
      isLabelled
        ? aggregateByLabels(allRawData)
        : {
            chartData: [],
            colorMap: new Map<string, string>(),
            labelValues: [],
          },
    [isLabelled, allRawData],
  )

  const envColorMap = useMemo(
    () => buildEnvColorMap(environmentIds),
    [environmentIds],
  )

  const labelOptions = useMemo(
    () => labelValues.map((v) => ({ label: v, value: v })),
    [labelValues],
  )

  const filteredLabels =
    selectedLabels.length > 0
      ? labelValues.filter((v) => selectedLabels.includes(v))
      : labelValues

  const handleEnvironmentChange = (value: string[] | string | undefined) => {
    if (!value || (Array.isArray(value) && value.length === 0)) {
      setEnvironmentIds(defaultEnvironmentIds)
    } else {
      setEnvironmentIds(Array.isArray(value) ? value : [value])
    }
  }

  const hasData = isLabelled
    ? labelledChartData.length > 0
    : data &&
      Array.isArray(data) &&
      data.length > 0 &&
      data.some((dayData) =>
        environmentIds.some((envId) => Number(dayData[envId] || 0) > 0),
      )

  return (
    <>
      <FormGroup className='mb-4'>
        <h5 className='mb-2'>Flag events for last 30 days</h5>
        <div className='d-flex gap-3 mb-3 flex-wrap'>
          <div className='flex-fill'>
            <EnvironmentTagSelect
              projectId={projectId}
              idField='id'
              value={environmentIds}
              multiple
              onChange={handleEnvironmentChange}
            />
          </div>
          {isLabelled && labelValues.length > 1 && (
            <div className='flex-fill' style={{ maxWidth: 400 }}>
              <MultiSelect
                label='Filter by SDK'
                options={labelOptions}
                selectedValues={selectedLabels}
                onSelectionChange={setSelectedLabels}
                colorMap={colorMap}
              />
            </div>
          )}
        </div>
        {isLoading && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        {!isLoading && !hasData && (
          <div
            style={{ height: 200 }}
            className='text-center justify-content-center align-items-center text-muted mt-4 d-flex'
          >
            No analytics data available for the selected environments
            {environmentIds?.length > 1 ? 's' : ''}.
          </div>
        )}
        {hasData && (
          <BarChart
            data={isLabelled ? labelledChartData : data || []}
            series={isLabelled ? filteredLabels : environmentIds}
            colorMap={isLabelled ? colorMap : envColorMap}
            xAxisInterval={2}
          />
        )}
      </FormGroup>
      <InfoMessage>
        The Flag Analytics data will be visible in the Dashboard between 30
        minutes and 1 hour after it has been collected.{' '}
        <a
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/flag-analytics'
          rel='noreferrer'
        >
          View docs
        </a>
      </InfoMessage>
    </>
  )
}

export default FlagAnalytics
