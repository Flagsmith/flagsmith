import React, { useMemo, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import BarChart, { ChartDataPoint } from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'

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
    Development: 1200,
    Production: 5000,
    Staging: 2400,
    'flagsmith-js-sdk': 4500,
    'flagsmith-python-sdk': 2200,
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
      const base = baseMap[label] || 800
      const variance = Math.floor(pseudoRandom(label, i) * base * 0.4)
      const weekday = date.getUTCDay()
      const weekendDip = weekday === 0 || weekday === 6 ? 0.4 : 1
      point[label] = Math.floor((base + variance) * weekendDip)
    })
    data.push(point)
  }
  return data
}

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
