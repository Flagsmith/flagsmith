import type { Meta, StoryObj } from 'storybook'
import MetricsComparisonTable from 'components/experiments-v2/shared/MetricsComparisonTable'
import { MOCK_EXPERIMENT_RESULT } from 'components/experiments-v2/types'

const meta: Meta<typeof MetricsComparisonTable> = {
  component: MetricsComparisonTable,
  tags: ['autodocs'],
  title: 'Experiments/MetricsComparisonTable',
}
export default meta

type Story = StoryObj<typeof MetricsComparisonTable>

export const WithSignificance: Story = {
  args: { metrics: MOCK_EXPERIMENT_RESULT.metrics },
}

export const NoSignificance: Story = {
  args: {
    metrics: MOCK_EXPERIMENT_RESULT.metrics.map((m) => ({
      ...m,
      isSignificant: false,
      liftDirection: 'neutral' as const,
      significance: 'not significant',
    })),
  },
}
