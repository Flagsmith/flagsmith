import React, { useMemo, useState } from 'react'
import { Res } from 'common/types/responses'
import SingleSDKLabelsChart from './components/SingleSDKLabelsChart'
import { MultiValueProps } from 'react-select/lib/components/MultiValue'

export interface OrganisationUsageMetricsProps {
  data?: Res['organisationUsage']
  selectedMetrics: string[]
}
export type ChartDataPoint = {
  day: any
} & Record<string, number>

const colours = [
  'rgba(37, 99, 235, 0.8)',
  'rgba(220, 38, 38, 0.8)',
  'rgba(22, 163, 74, 0.8)',
  'rgba(234, 88, 12, 0.8)',
  'rgba(124, 58, 237, 0.8)',
  'rgba(8, 145, 178, 0.8)',
  'rgba(219, 39, 119, 0.8)',
  'rgba(132, 204, 22, 0.8)',
  'rgba(245, 158, 11, 0.8)',
  'rgba(139, 92, 246, 0.8)',
  'rgba(6, 182, 212, 0.8)',
  'rgba(244, 114, 182, 0.8)',
  'rgba(16, 185, 129, 0.8)',
  'rgba(249, 115, 22, 0.8)',
  'rgba(99, 102, 241, 0.8)',
  'rgba(239, 68, 68, 0.8)',
  'rgba(34, 197, 94, 0.8)',
  'rgba(168, 85, 247, 0.8)',
  'rgba(20, 184, 166, 0.8)',
  'rgba(234, 179, 8, 0.8)',
]

const OrganisationUsageMetrics: React.FC<OrganisationUsageMetricsProps> = ({
  data,
  selectedMetrics,
}) => {
  const [selectedUserAgents, setSelectedUserAgents] = useState<string[]>([])

  const {
    environmentDocumentChartData,
    flagsChartData,
    identitiesChartData,
    traitsChartData,
    userAgentColorMap,
  } = useMemo(() => {
    if (!data?.events_list)
      return {
        environmentDocumentChartData: [],
        flagsChartData: [],
        identitiesChartData: [],
        traitsChartData: [],
      }

    const flagsGrouped: Record<string, ChartDataPoint> = {}
    const identitiesGrouped: Record<string, ChartDataPoint> = {}
    const environmentDocumentGrouped: Record<string, ChartDataPoint> = {}
    const traitsGrouped: Record<string, ChartDataPoint> = {}
    const userAgents = new Set<string>()

    data.events_list.forEach((event) => {
      const date = event.day
      const userAgent = event.labels?.user_agent || 'Unknown'
      userAgents.add(userAgent)

      if (!flagsGrouped[date])
        flagsGrouped[date] = { day: date } as ChartDataPoint
      if (!identitiesGrouped[date])
        identitiesGrouped[date] = { day: date } as ChartDataPoint
      if (!environmentDocumentGrouped[date])
        environmentDocumentGrouped[date] = { day: date } as ChartDataPoint
      if (!traitsGrouped[date])
        traitsGrouped[date] = { day: date } as ChartDataPoint

      flagsGrouped[date][userAgent] =
        (flagsGrouped[date][userAgent] || 0) + (event.flags || 0)
      identitiesGrouped[date][userAgent] =
        (identitiesGrouped[date][userAgent] || 0) + (event.identities || 0)
      environmentDocumentGrouped[date][userAgent] =
        (environmentDocumentGrouped[date][userAgent] || 0) +
        (event.environment_document || 0)
      traitsGrouped[date][userAgent] =
        (traitsGrouped[date][userAgent] || 0) + (event.traits || 0)
    })

    const colorMap = new Map()
    Array.from(userAgents).forEach((agent, index) => {
      colorMap.set(agent, colours[index % colours.length])
    })

    return {
      environmentDocumentChartData: Object.values(environmentDocumentGrouped),
      flagsChartData: Object.values(flagsGrouped),
      identitiesChartData: Object.values(identitiesGrouped),
      traitsChartData: Object.values(traitsGrouped),
      userAgentColorMap: colorMap,
    }
  }, [data?.events_list])

  const allUserAgents = useMemo(() => {
    if (!data?.events_list) return []
    return [
      ...new Set(
        data.events_list.map((e) => e.labels?.user_agent || 'Unknown'),
      ),
    ]
  }, [data?.events_list])
  const userAgentOptions = useMemo(() => {
    return allUserAgents.map((agent) => ({
      label: agent,
      value: agent,
    }))
  }, [allUserAgents])

  const chartItems = [
    {
      data: flagsChartData,
      metricKey: 'flags',
      title: 'Flags',
      userAgents: allUserAgents,
      visible: selectedMetrics?.includes('Flags'),
    },
    {
      data: identitiesChartData,
      metricKey: 'identities',
      title: 'Identities',
      userAgents: allUserAgents,
      visible: selectedMetrics?.includes('Identities'),
    },
    {
      data: environmentDocumentChartData,
      metricKey: 'environmentDocuments',
      title: 'Environment Documents',
      userAgents: allUserAgents,
      visible: selectedMetrics?.includes('Environment Document'),
    },
    {
      data: traitsChartData,
      metricKey: 'traits',
      title: 'Traits',
      userAgents: allUserAgents,
      visible: selectedMetrics?.includes('Traits'),
    },
  ]

  const CustomMultiValue = ({
    data,
    removeProps,
  }: MultiValueProps<{ label: string; value: string }>) => {
    const backgroundColor = userAgentColorMap?.get(data.value) || colours[0]

    return (
      <div
        className='d-flex align-items-center'
        style={{
          backgroundColor,
          borderRadius: '4px',
          color: 'white',
          fontSize: '12px',
          maxWidth: '150px',
          overflow: 'hidden',
          padding: '2px 6px',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        <span
          className='mr-1'
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {data.label}
        </span>
        <span
          onClick={() => removeProps?.onClick?.(data)}
          style={{
            cursor: 'pointer',
            fontSize: '14px',
            lineHeight: '1',
          }}
        >
          ×
        </span>
      </div>
    )
  }

  return (
    <div className='row'>
      <div className='col-12 mb-4'>
        <div className='row'>
          <div className='col-12'>
            <label>Filter SDKs</label>
            <Select
              isMulti
              closeMenuOnSelect={false}
              placeholder='Select SDKs to display...'
              onChange={(selectedOptions: any) => {
                const values = selectedOptions
                  ? selectedOptions.map((opt: any) => opt.value)
                  : []
                setSelectedUserAgents(values)
              }}
              components={{
                MultiValue: CustomMultiValue,
              }}
              value={selectedUserAgents.map((agent) => ({
                label: agent,
                value: agent,
              }))}
              options={userAgentOptions}
              className='react-select react-select__extensible'
              styles={{
                container: (base: any) => ({
                  ...base,
                  maxWidth: '100%',
                  minWidth: '300px',
                  width: 'fit-content',
                }),
                control: (base: any) => ({
                  ...base,
                  height: 'auto',
                  minHeight: '44px',
                  minWidth: '300px',
                  width: 'fit-content',
                }),
                multiValue: (base: any) => ({
                  ...base,
                  flexShrink: 0,
                  margin: '2px',
                }),
                valueContainer: (base: any) => ({
                  ...base,
                  flexWrap: 'wrap',
                  gap: '4px',
                  overflow: 'visible',
                  paddingBottom: '6px',
                  paddingTop: '6px',
                }),
              }}
            />
          </div>
        </div>
      </div>
      {chartItems
        .filter((chart) => chart.visible)
        .map((chart) => {
          const filteredUserAgents =
            selectedUserAgents.length > 0
              ? chart.userAgents?.filter((userAgent: string) =>
                  selectedUserAgents.includes(userAgent),
                )
              : chart.userAgents
          return (
            <div className='col-12 mb-4' key={chart.metricKey}>
              <SingleSDKLabelsChart
                data={chart.data}
                userAgents={filteredUserAgents}
                metricKey={chart.metricKey}
                title={chart.title}
                colours={colours}
                userAgentsColorMap={userAgentColorMap}
              />
            </div>
          )
        })}
    </div>
  )
}

export default OrganisationUsageMetrics
