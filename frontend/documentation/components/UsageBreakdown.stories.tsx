import type { Meta, StoryObj } from 'storybook'
import UsageBreakdown from 'components/organisation-settings/usage/UsageBreakdown'

const meta: Meta<typeof UsageBreakdown> = {
  args: { onChangeDimension: () => {} },
  component: UsageBreakdown,
  title: 'Pages/Usage Dashboard/Components/UsageBreakdown',
}
export default meta

type Story = StoryObj<typeof UsageBreakdown>

export const ByRequestType: Story = {
  args: {
    dimension: 'request-type',
    rows: [
      { label: 'Flags', value: 5_240_000 },
      { label: 'Environment Document', value: 1_910_000 },
      { label: 'Identities', value: 730_000 },
      { label: 'Traits', value: 120_000 },
    ],
  },
}

/** One row dwarfing the rest is the common shape, so the bars must still read. */
export const OneDominantRow: Story = {
  args: {
    dimension: 'request-type',
    rows: [
      { label: 'Flags', value: 8_900_000 },
      { label: 'Identities', value: 41_000 },
      { label: 'Traits', value: 9_000 },
    ],
  },
}

export const BySdk: Story = {
  args: {
    dimension: 'sdk',
    rows: [
      { label: 'flagsmith-python/3.9.1', value: 3_100_000 },
      { label: 'flagsmith-java/7.2.0', value: 2_450_000 },
      { label: 'flagsmith-nodejs/5.0.4', value: 980_000 },
      { label: 'Unknown', value: 210_000 },
    ],
  },
}

export const ByProject: Story = {
  args: {
    dimension: 'project',
    rows: [
      { label: 'Checkout', value: 4_120_000 },
      { label: 'Mobile app', value: 2_060_000 },
      { label: 'Internal tools', value: 88_000 },
    ],
  },
}

/** Environments belong to a project, so the dimension asks for one first. */
export const EnvironmentWithoutAProject: Story = {
  args: { dimension: 'environment', needsProject: true, rows: [] },
}

export const Loading: Story = {
  args: { dimension: 'project', isLoading: true, rows: [] },
}

export const NoUsageRecorded: Story = {
  args: { dimension: 'request-type', rows: [] },
}
