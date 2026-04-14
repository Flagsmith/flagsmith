import React, { FC, useEffect, useMemo, useState } from 'react'
import EmptyState from 'components/EmptyState'
import InfoMessage from 'components/InfoMessage'
import EnvironmentTagSelect from 'components/EnvironmentTagSelect'
import BarChart from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import { useGetFeatureAnalyticsQuery } from 'common/services/useFeatureAnalytics'
import { aggregateByLabels, hasLabelledData } from './utils'
import { useEnvChartProps } from './useEnvChartProps'

type FlagAnalyticsType = {
  projectId: number
  featureId: number
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

  // Clear SDK filter when labelled mode deactivates (e.g. user switches to
  // an env with no labels) — avoids stale chips in a disabled MultiSelect.
  useEffect(() => {
    if (!isLabelled) setSelectedLabels([])
  }, [isLabelled])

  const envChart = useEnvChartProps({ environmentIds, projectId })

  // Labelled-mode derivations — inline useMemos (component-local, no reuse
  // elsewhere, so not worth extracting into a hook).
  const {
    chartData: labelledChartData,
    colorMap: labelColorMap,
    labelValues,
  } = useMemo(
    () =>
      isLabelled && data?.rawEntries && data?.chartData
        ? aggregateByLabels(
            data.rawEntries,
            data.chartData.map((d) => d.day),
          )
        : { chartData: [], colorMap: {}, labelValues: [] },
    [isLabelled, data?.rawEntries, data?.chartData],
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

  // labelledChartData has one bucket per day (including empties), so a plain
  // length check isn't meaningful — probe for any non-zero series value.
  const hasData = isLabelled
    ? labelledChartData.some((dayData) =>
        labelValues.some((v) => Number(dayData[v] || 0) > 0),
      )
    : data?.chartData &&
      data.chartData.length > 0 &&
      data.chartData.some((dayData) =>
        envChart.series.some((envId) => Number(dayData[envId] || 0) > 0),
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
          <MultiSelect
            className='w-100'
            label='Filter by SDK'
            options={labelOptions}
            selectedValues={selectedLabels}
            onSelectionChange={setSelectedLabels}
            colorMap={labelColorMap}
            disabled={!isLabelled || labelValues.length <= 1}
          />
        </div>
        {isLoading && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        {!isLoading && !hasData && (
          <EmptyState
            title='No analytics data'
            description={`No evaluation data available for the selected environment${
              environmentIds?.length > 1 ? 's' : ''
            }.`}
            icon='bar-chart'
          />
        )}
        {hasData &&
          (isLabelled ? (
            <BarChart
              data={labelledChartData}
              series={filteredLabels}
              colorMap={labelColorMap}
              xAxisInterval={2}
              showLegend
            />
          ) : (
            <BarChart
              data={data?.chartData || []}
              series={envChart.series}
              colorMap={envChart.colorMap}
              seriesLabels={envChart.seriesLabels}
              xAxisInterval={2}
            />
          ))}
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
