import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import SelectMetricsStep from 'components/experiments-v2/steps/SelectMetricsStep'
import { Metric, MOCK_METRICS } from 'components/experiments-v2/types'

const meta: Meta<typeof SelectMetricsStep> = {
  component: SelectMetricsStep,
  decorators: [
    (Story) => (
      <div style={{ maxWidth: 600 }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
  title: 'Experiments/Steps/SelectMetricsStep',
}
export default meta

type Story = StoryObj<typeof SelectMetricsStep>

export const NoneSelected: Story = {
  args: {
    onToggleMetric: () => {},
    selectedMetrics: [],
  },
}

export const WithMetrics: Story = {
  args: {
    onToggleMetric: () => {},
    selectedMetrics: [
      MOCK_METRICS[0],
      { ...MOCK_METRICS[1], role: 'secondary' },
    ],
  },
}

export const Interactive: Story = {
  decorators: [
    () => {
      const [selected, setSelected] = useState<Metric[]>([])
      const handleToggle = (metric: Metric) => {
        const exists = selected.find((m) => m.id === metric.id)
        if (exists) {
          setSelected(selected.filter((m) => m.id !== metric.id))
        } else {
          const role = selected.length === 0 ? 'primary' : 'secondary'
          setSelected([...selected, { ...metric, role }])
        }
      }
      return (
        <SelectMetricsStep
          selectedMetrics={selected}
          onToggleMetric={handleToggle}
        />
      )
    },
  ],
}
