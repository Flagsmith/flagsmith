import React, { useMemo, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import BarChart, { ChartDataPoint } from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import { CHART_COLOURS } from 'common/theme/tokens'
import { getCSSVars } from 'common/utils/getCSSVar'

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

function generateFakeData(days: number, labels: string[]): ChartDataPoint[] {
  const data: ChartDataPoint[] = []
  const now = new Date()

  const baseMap: Record<string, number> = {
    Development: 1200,
    Production: 5000,
    Staging: 2400,
    'flagsmith-js-sdk': 4500,
    'flagsmith-python-sdk': 2200,
  }

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const dayStr = date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
    })

    const point: ChartDataPoint = { day: dayStr }
    labels.forEach((label) => {
      const base = baseMap[label] || 800
      const variance = Math.floor(Math.random() * base * 0.4)
      const weekday = (now.getDay() - i + 7) % 7
      const weekendDip = weekday === 0 || weekday === 6 ? 0.4 : 1
      point[label] = Math.floor((base + variance) * weekendDip)
    })
    data.push(point)
  }
  return data
}

function buildColorMap(labels: string[]): Map<string, string> {
  const resolved = getCSSVars(CHART_COLOURS)
  const map = new Map<string, string>()
  labels.forEach((label, i) => {
    map.set(label, resolved[i % resolved.length])
  })
  return map
}

// ============================================================================
// Stories
// ============================================================================

const meta: Meta<typeof BarChart> = {
  component: BarChart,
  tags: ['autodocs'],
  title: 'Components/BarChart',
}
export default meta

type Story = StoryObj<typeof BarChart>

export const WithLabelledBuckets: Story = {
  decorators: [
    () => {
      const labels = useMemo(() => SDKS.slice(0, 5), [])
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildColorMap(labels), [labels])
      const [selectedLabels, setSelectedLabels] = useState<string[]>([])

      const filteredLabels =
        selectedLabels.length > 0
          ? labels.filter((l) => selectedLabels.includes(l))
          : labels

      const labelOptions = labels.map((l) => ({ label: l, value: l }))

      return (
        <div style={{ maxWidth: 900 }}>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 13,
              marginBottom: 16,
            }}
          >
            Stacked by SDK label — each color represents a different SDK sending
            evaluations.
          </p>
          <div style={{ marginBottom: 16, maxWidth: 400 }}>
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
      const colorMap = useMemo(() => buildColorMap(labels), [labels])

      return (
        <div style={{ maxWidth: 900 }}>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 13,
              marginBottom: 16,
            }}
          >
            No labels — grouped by environment (current behaviour).
          </p>
          <BarChart
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

export const SingleSeries: Story = {
  decorators: [
    () => {
      const labels = useMemo(() => ['flagsmith-js-sdk'], [])
      const data = useMemo(() => generateFakeData(30, labels), [labels])
      const colorMap = useMemo(() => buildColorMap(labels), [labels])

      return (
        <div style={{ maxWidth: 900 }}>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 13,
              marginBottom: 16,
            }}
          >
            Single SDK — no filter needed when there's only one series.
          </p>
          <BarChart
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
