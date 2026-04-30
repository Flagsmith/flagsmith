import React from 'react'
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

const STAGE_COLOR_MAP = buildChartColorMap(STAGE_DATA.map((s) => s.name))
const SDK_COLOR_MAP = buildChartColorMap(SDK_DATA.map((s) => s.name))
const TWO_SLICE_COLOR_MAP = buildChartColorMap(
  TWO_SLICE_DATA.map((s) => s.name),
)

// ============================================================================
// Stories
// ============================================================================

const meta: Meta<typeof PieChart> = {
  component: PieChart,
  tags: ['autodocs'],
  title: 'Components/Charts/PieChart',
}
export default meta

type Story = StoryObj<typeof PieChart>

export const Donut: Story = {
  decorators: [
    () => (
      <div className='d-flex justify-content-center'>
        <div style={{ width: 240 }}>
          <p className='text-secondary fs-small mb-3 text-center'>
            Donut variant — inner cutout for a secondary label or count.
          </p>
          <PieChart
            data={STAGE_DATA}
            colorMap={STAGE_COLOR_MAP}
            height={240}
            innerRadius={60}
            outerRadius={100}
          />
        </div>
      </div>
    ),
  ],
}

export const SolidPie: Story = {
  decorators: [
    () => (
      <div className='d-flex justify-content-center'>
        <div style={{ width: 240 }}>
          <p className='text-secondary fs-small mb-3 text-center'>
            Solid pie — no inner radius.
          </p>
          <PieChart
            data={STAGE_DATA}
            colorMap={STAGE_COLOR_MAP}
            height={240}
            outerRadius={100}
          />
        </div>
      </div>
    ),
  ],
}

export const TwoSlices: Story = {
  decorators: [
    () => (
      <div className='d-flex justify-content-center'>
        <div style={{ width: 220 }}>
          <p className='text-secondary fs-small mb-3 text-center'>
            Minimal case — two slices for a released vs. in-progress split.
          </p>
          <PieChart
            data={TWO_SLICE_DATA}
            colorMap={TWO_SLICE_COLOR_MAP}
            height={220}
            innerRadius={60}
            outerRadius={90}
          />
        </div>
      </div>
    ),
  ],
}

export const ManySlices: Story = {
  decorators: [
    () => (
      <div className='d-flex justify-content-center'>
        <div style={{ width: 300 }}>
          <p className='text-secondary fs-small mb-3 text-center'>
            Seven slices — stress-test of the colour palette.
          </p>
          <PieChart
            data={SDK_DATA}
            colorMap={SDK_COLOR_MAP}
            height={380}
            innerRadius={60}
            outerRadius={100}
            showLegend
          />
        </div>
      </div>
    ),
  ],
}

export const WithLegend: Story = {
  decorators: [
    () => (
      <div className='d-flex justify-content-center'>
        <div style={{ width: 300 }}>
          <p className='text-secondary fs-small mb-3 text-center'>
            Legend enabled — useful when slices are many or narrow.
          </p>
          <PieChart
            data={STAGE_DATA}
            colorMap={STAGE_COLOR_MAP}
            height={340}
            innerRadius={60}
            outerRadius={100}
            showLegend
          />
        </div>
      </div>
    ),
  ],
}
