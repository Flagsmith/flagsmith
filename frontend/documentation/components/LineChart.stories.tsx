import React, { useMemo } from 'react'
import type { Meta, StoryObj } from 'storybook'
import LineChart from 'components/charts/LineChart'
import { ChartDataPoint } from 'components/charts/BarChart'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'

// ============================================================================
// Fake data
// ============================================================================

// Deterministic stand-in for Math.random — same `(label, day)` pair always
// produces the same value, so Chromatic snapshots stay stable across runs.
const pseudoRandom = (label: string, day: number): number => {
  let hash = 0
  const seed = `${label}-${day}`
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash) / 0x7fffffff
}

// Pinned reference date — using `new Date()` would shift the x-axis daily and
// drift every Chromatic snapshot.
const REFERENCE_DATE = new Date('2026-04-15T00:00:00Z')

function generateFakeData(days: number, labels: string[]): ChartDataPoint[] {
  const data: ChartDataPoint[] = []

  const baseMap: Record<string, number> = {
    'API Calls': 12000,
    Clicks: 2000,
    Conversions: 800,
    Errors: 80,
    'Flag Evaluations': 8000,
    'Identity Requests': 5000,
    'Page Views': 15000,
  }

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(REFERENCE_DATE)
    date.setUTCDate(date.getUTCDate() - i)
    const dayStr = date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      timeZone: 'UTC',
    })

    const point: ChartDataPoint = { day: dayStr }
    labels.forEach((label) => {
      const base = baseMap[label] || 1000
      const variance = Math.floor(pseudoRandom(label, i) * base * 0.35)
      const weekday = date.getUTCDay()
      const weekendDip = weekday === 0 || weekday === 6 ? 0.6 : 1
      point[label] = Math.floor((base + variance) * weekendDip)
    })
    data.push(point)
  }
  return data
}

// ============================================================================
// Stories
// ============================================================================

const meta: Meta<typeof LineChart> = {
  component: LineChart,
  tags: ['autodocs'],
  title: 'Components/LineChart',
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
