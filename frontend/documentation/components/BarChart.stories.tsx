import React, { useMemo, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import BarChart from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'
import { generateChartFakeData } from './_chartFakeData'

// ============================================================================
// Fake data
// ============================================================================

const SDKS = [
  'flagsmith-js-sdk',
  'flagsmith-python-sdk',
  'flagsmith-java-sdk',
  'flagsmith-go-sdk',
  'flagsmith-ruby-sdk',
]

const BAR_BASE_MAP: Record<string, number> = {
  Development: 1200,
  Production: 5000,
  Staging: 2400,
  'flagsmith-js-sdk': 4500,
  'flagsmith-python-sdk': 2200,
}

const generateFakeData = (days: number, labels: string[]) =>
  generateChartFakeData({
    baseMap: BAR_BASE_MAP,
    days,
    defaultBase: 800,
    labels,
    variance: 0.4,
    weekendDip: 0.4,
  })

// ============================================================================
// Stories
// ============================================================================

const meta: Meta<typeof BarChart> = {
  component: BarChart,
  tags: ['autodocs'],
  title: 'Components/Charts/BarChart',
}
export default meta

type Story = StoryObj<typeof BarChart>

export const WithLabelledBuckets: Story = {
  decorators: [
    () => {
      const labels = useMemo(() => SDKS.slice(0, 5), [])
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildChartColorMap(labels), [labels])
      const [selectedLabels, setSelectedLabels] = useState<string[]>([])

      const filteredLabels =
        selectedLabels.length > 0
          ? labels.filter((l) => selectedLabels.includes(l))
          : labels

      const labelOptions = labels.map((l) => ({ label: l, value: l }))

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            Stacked by SDK label — each color represents a different SDK sending
            evaluations.
          </p>
          <div className='mb-3' style={{ maxWidth: 400 }}>
            <MultiSelect
              label='Filter by SDK'
              options={labelOptions}
              selectedValues={selectedLabels}
              onSelectionChange={setSelectedLabels}
              colorMap={colorMap}
            />
          </div>
          <BarChart
            data={data}
            series={filteredLabels}
            colorMap={colorMap}
            xAxisInterval={2}
            showLegend
          />
        </div>
      )
    },
  ],
}

export const WithoutLabels: Story = {
  decorators: [
    () => {
      const labels = useMemo(() => ['Production', 'Staging', 'Development'], [])
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildChartColorMap(labels), [labels])

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            No labels — grouped by environment (current behaviour).
          </p>
          <BarChart
            data={data}
            series={labels}
            colorMap={colorMap}
            xAxisInterval={2}
            showLegend
          />
        </div>
      )
    },
  ],
}

export const SingleSeries: Story = {
  decorators: [
    () => {
      const labels = useMemo(() => ['flagsmith-js-sdk'], [])
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildChartColorMap(labels), [labels])

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            Single SDK — no filter needed when there's only one series.
          </p>
          <BarChart
            data={data}
            series={labels}
            colorMap={colorMap}
            xAxisInterval={2}
            showLegend
          />
        </div>
      )
    },
  ],
}
