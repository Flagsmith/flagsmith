import React, { FC, useMemo, useState } from 'react'
import InfoMessage from 'components/InfoMessage'
import EnvironmentTagSelect from 'components/EnvironmentTagSelect'
import BarChart from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import { useGetFeatureAnalyticsQuery } from 'common/services/useFeatureAnalytics'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'
import { aggregateByLabels, hasLabelledData } from './utils'

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

  const isLabelled = hasLabelledData(data?.rawEntries)

  const {
    chartData: labelledChartData,
    colorMap,
    labelValues,
  } = useMemo(
    () =>
      isLabelled && data?.rawEntries && data?.chartData
        ? aggregateByLabels(
            data.rawEntries,
            data.chartData.map((d) => d.day),
          )
        : {
            chartData: [],
            colorMap: new Map<string, string>(),
            labelValues: [],
          },
    [isLabelled, data?.rawEntries, data?.chartData],
  )

  const envColorMap = useMemo(
    () => buildChartColorMap(environmentIds),
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

  // labelledChartData now always has one bucket per day (even when empty),
  // so we can't use `.length > 0` — check that at least one day has a
  // non-zero count for one of the label series.
  const hasData = isLabelled
    ? labelledChartData.some((dayData) =>
        labelValues.some((v) => Number(dayData[v] || 0) > 0),
      )
    : data?.chartData &&
      data.chartData.length > 0 &&
      data.chartData.some((dayData) =>
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
            No analytics data available for the selected environment
            {environmentIds?.length > 1 ? 's' : ''}.
          </div>
        )}
        {hasData && (
          <BarChart
            data={isLabelled ? labelledChartData : data?.chartData || []}
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
