import type { Meta, StoryObj } from 'storybook'
import UsageBar from 'components/shared/UsageBar'

const meta: Meta<typeof UsageBar> = {
  component: UsageBar,
  parameters: { layout: 'padded' },
  title: 'Components/Data Display/UsageBar',
}
export default meta

type Story = StoryObj<typeof UsageBar>

export const WithLabel: Story = {
  args: { label: 'Segment overrides', limit: 100, usage: 42 },
}

export const Warning: Story = {
  args: { label: 'Segment overrides', limit: 100, usage: 91 },
}

export const OverTheLimit: Story = {
  args: { label: 'Segment overrides', limit: 100, usage: 118 },
}

// Thresholds are marked on the bar, for usage that is notified at set points.
export const WithThresholds: Story = {
  args: {
    ariaLabel: 'Plan usage this period',
    limit: 2000000,
    thresholds: [75, 100],
    usage: 1240000,
    warnAt: 75,
  },
}

export const WithThresholdsOverTheLimit: Story = {
  args: {
    ariaLabel: 'Plan usage this period',
    limit: 50000,
    thresholds: [75, 100],
    usage: 68400,
    warnAt: 75,
  },
}

export const NoUsageYet: Story = {
  args: { label: 'Segment overrides', limit: 100, usage: 0 },
}
