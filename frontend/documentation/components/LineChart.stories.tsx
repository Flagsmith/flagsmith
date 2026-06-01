import React, { useMemo } from 'react'
import type { Meta, StoryObj } from 'storybook'
import LineChart from 'components/charts/LineChart'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'
import { generateChartFakeData } from './_chartFakeData'

// ============================================================================
// Fake data
// ============================================================================

const LINE_BASE_MAP: Record<string, number> = {
  'API Calls': 12000,
  Clicks: 2000,
  Conversions: 800,
  Errors: 80,
  'Flag Evaluations': 8000,
  'Identity Requests': 5000,
  'Page Views': 15000,
}

const generateFakeData = (days: number, labels: string[]) =>
  generateChartFakeData({
    baseMap: LINE_BASE_MAP,
    days,
    labels,
  })

// ============================================================================
// Stories
// ============================================================================

const meta: Meta<typeof LineChart> = {
  component: LineChart,
  tags: ['autodocs'],
  title: 'Components/Charts/LineChart',
}
export default meta

type Story = StoryObj<typeof LineChart>

export const UsageTrends: Story = {
  decorators: [
    () => {
      const labels = useMemo(
        () => ['API Calls', 'Flag Evaluations', 'Identity Requests'],
        [],
      )
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildChartColorMap(labels), [labels])

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            Mirrors the API Usage Trends dashboard — three independent metrics
            plotted over 30 days.
          </p>
          <LineChart
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

export const SingleLine: Story = {
  decorators: [
    () => {
      const labels = useMemo(() => ['API Calls'], [])
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildChartColorMap(labels), [labels])

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            One metric over time — legend hidden since the series is obvious
            from the chart title.
          </p>
          <LineChart
            data={data}
            series={labels}
            colorMap={colorMap}
            xAxisInterval={2}
          />
        </div>
      )
    },
  ],
}

export const ManyLines: Story = {
  decorators: [
    () => {
      const labels = useMemo(
        () => [
          'API Calls',
          'Flag Evaluations',
          'Identity Requests',
          'Page Views',
          'Clicks',
          'Conversions',
          'Errors',
        ],
        [],
      )
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildChartColorMap(labels), [labels])

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            Seven lines — stress-test of the colour palette.
          </p>
          <LineChart
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
