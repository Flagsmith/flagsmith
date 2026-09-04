import React, { useMemo, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import BarChart from 'components/charts/BarChart'
import { MultiSelect } from 'components/base/select/multi-select'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'
import { toBarSeries } from 'components/charts/toBarSeries'
import type { BarSeries, ChartDataPoint } from 'components/charts/types'
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

// Cumulative exposures per variant with a fixed share converted, the shape the
// experiment conversion chart plots: the faded segment is the remainder, so the
// full bar is the denominator and the solid part is the numerator.
const CONVERSION_SHARE: Record<string, number> = {
  control: 0.12,
  variant_a: 0.21,
}

const buildPartOfWholeData = (): ChartDataPoint[] => {
  const variants = Object.keys(CONVERSION_SHARE)
  const running: Record<string, number> = { control: 0, variant_a: 0 }
  return generateChartFakeData({
    days: 14,
    defaultBase: 300,
    labels: variants,
    variance: 0.6,
  }).map((point) => {
    const stacked: ChartDataPoint = { day: point.day }
    variants.forEach((key) => {
      running[key] += Number(point[key])
      const converted = Math.round(running[key] * CONVERSION_SHARE[key])
      stacked[key] = converted
      stacked[`${key}-rest`] = running[key] - converted
    })
    return stacked
  })
}

const buildPartOfWholeSeries = (): BarSeries[] => {
  const colours = buildChartColorMap(Object.keys(CONVERSION_SHARE))
  return [
    { key: 'control', label: 'Control converted', name: 'Control' },
    { key: 'variant_a', label: 'Variant A converted', name: 'Variant A' },
  ].flatMap(({ key, label, name }) => [
    { colour: colours[key], key, label, stackId: key },
    {
      colour: colours[key],
      key: `${key}-rest`,
      label: `${name} exposures`,
      opacity: 0.25,
      stackId: key,
    },
  ])
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
            series={toBarSeries(filteredLabels, colorMap)}
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
            series={toBarSeries(labels, colorMap)}
            xAxisInterval={2}
            showLegend
          />
        </div>
      )
    },
  ],
}

export const PartOfWholeStacks: Story = {
  decorators: [
    () => {
      const data = useMemo(() => buildPartOfWholeData(), [])
      const series = useMemo(() => buildPartOfWholeSeries(), [])
      const counts = (label: string, key: string) => {
        const point = data.find((p) => p.day === label)
        const converted = Number(point?.[key.replace('-rest', '')] ?? 0)
        const rest = Number(point?.[`${key.replace('-rest', '')}-rest`] ?? 0)
        return { converted, exposed: converted + rest }
      }

      return (
        <div className='mx-auto' style={{ maxWidth: 900 }}>
          <p className='text-secondary fs-small mb-3'>
            Part-of-whole stacks: cumulative exposures per variant with the
            converted share filled in.
          </p>
          <BarChart
            data={data}
            series={series}
            xAxisInterval={2}
            showLegend
            tooltip={{
              formatValue: (value, seriesKey, label) => {
                const { converted, exposed } = counts(label, seriesKey)
                if (seriesKey.endsWith('-rest')) return exposed.toLocaleString()
                const rate = exposed ? (converted / exposed) * 100 : 0
                return `${converted.toLocaleString()} of ${exposed.toLocaleString()} (${rate.toFixed(
                  1,
                )}%)`
              },
            }}
          />
        </div>
      )
    },
  ],
  parameters: {
    docs: {
      description: {
        story:
          "Series sharing a `stackId` stack into one bar; distinct ids sit side by side. Giving the remainder segment an `opacity` fades it, and the legend swatch fades with it (recharts' own legend swatch ignores `fillOpacity`, so the chart renders its own key). `tooltip.formatValue` reports the pair, and a formatted value hides the total row by default since it is no longer additive.",
      },
    },
  },
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
            series={toBarSeries(labels, colorMap)}
            xAxisInterval={2}
            showLegend
          />
        </div>
      )
    },
  ],
}
