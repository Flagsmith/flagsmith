import React, { useMemo } from 'react'
import type { Meta, StoryObj } from 'storybook'
import PieChart, { PieSlice } from 'components/charts/PieChart'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'

// ============================================================================
// Fake data
// ============================================================================

const STAGE_DATA: PieSlice[] = [
  { name: 'Development', value: 12 },
  { name: 'Staging', value: 8 },
  { name: 'Pre-production', value: 5 },
  { name: 'Production', value: 15 },
  { name: 'Released', value: 32 },
]

const SDK_DATA: PieSlice[] = [
  { name: 'flagsmith-js-sdk', value: 4500 },
  { name: 'flagsmith-python-sdk', value: 2200 },
  { name: 'flagsmith-java-sdk', value: 1100 },
  { name: 'flagsmith-go-sdk', value: 800 },
  { name: 'flagsmith-ruby-sdk', value: 400 },
  { name: 'flagsmith-dotnet-sdk', value: 300 },
  { name: 'flagsmith-rust-sdk', value: 150 },
]

const TWO_SLICE_DATA: PieSlice[] = [
  { name: 'Released', value: 32 },
  { name: 'In progress', value: 18 },
]

// ============================================================================
// Stories
// ============================================================================

const meta: Meta<typeof PieChart> = {
  component: PieChart,
  tags: ['autodocs'],
  title: 'Components/PieChart',
}
export default meta

type Story = StoryObj<typeof PieChart>

export const Donut: Story = {
  decorators: [
    () => {
      const data = STAGE_DATA
      const colorMap = useMemo(
        () => buildChartColorMap(data.map((s) => s.name)),
        [data],
      )
      return (
        <div className='d-flex justify-content-center'>
          <div style={{ width: 240 }}>
            <p className='text-secondary fs-small mb-3 text-center'>
              Donut variant — inner cutout for a secondary label or count.
            </p>
            <PieChart
              data={data}
              colorMap={colorMap}
              height={240}
              innerRadius={60}
              outerRadius={100}
            />
          </div>
        </div>
      )
    },
  ],
}

export const SolidPie: Story = {
  decorators: [
    () => {
      const data = STAGE_DATA
      const colorMap = useMemo(
        () => buildChartColorMap(data.map((s) => s.name)),
        [data],
      )
      return (
        <div className='d-flex justify-content-center'>
          <div style={{ width: 240 }}>
            <p className='text-secondary fs-small mb-3 text-center'>
              Solid pie — no inner radius.
            </p>
            <PieChart
              data={data}
              colorMap={colorMap}
              height={240}
              outerRadius={100}
            />
          </div>
        </div>
      )
    },
  ],
}

export const TwoSlices: Story = {
  decorators: [
    () => {
      const data = TWO_SLICE_DATA
      const colorMap = useMemo(
        () => buildChartColorMap(data.map((s) => s.name)),
        [data],
      )
      return (
        <div className='d-flex justify-content-center'>
          <div style={{ width: 220 }}>
            <p className='text-secondary fs-small mb-3 text-center'>
              Minimal case — two slices for a released vs. in-progress split.
            </p>
            <PieChart
              data={data}
              colorMap={colorMap}
              height={220}
              innerRadius={60}
              outerRadius={90}
            />
          </div>
        </div>
      )
    },
  ],
}

export const ManySlices: Story = {
  decorators: [
    () => {
      const data = SDK_DATA
      const colorMap = useMemo(
        () => buildChartColorMap(data.map((s) => s.name)),
        [data],
      )
      return (
        <div className='d-flex justify-content-center'>
          <div style={{ width: 300 }}>
            <p className='text-secondary fs-small mb-3 text-center'>
              Seven slices — stress-test of the colour palette.
            </p>
            <PieChart
              data={data}
              colorMap={colorMap}
              height={380}
              innerRadius={60}
              outerRadius={100}
              showLegend
            />
          </div>
        </div>
      )
    },
  ],
}

export const WithLegend: Story = {
  decorators: [
    () => {
      const data = STAGE_DATA
      const colorMap = useMemo(
        () => buildChartColorMap(data.map((s) => s.name)),
        [data],
      )
      return (
        <div className='d-flex justify-content-center'>
          <div style={{ width: 300 }}>
            <p className='text-secondary fs-small mb-3 text-center'>
              Legend enabled — useful when slices are many or narrow.
            </p>
            <PieChart
              data={data}
              colorMap={colorMap}
              height={340}
              innerRadius={60}
              outerRadius={100}
              showLegend
            />
          </div>
        </div>
      )
    },
  ],
}
