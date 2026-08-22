import type { Meta, StoryObj } from 'storybook'
import { UsageBreakdownView } from 'components/organisation-settings/usage/UsageBreakdown'

const meta: Meta<typeof UsageBreakdownView> = {
  args: { onChangeDimension: () => {} },
  component: UsageBreakdownView,
  title: 'Pages/Usage Dashboard/Components/UsageBreakdown',
}
export default meta

type Story = StoryObj<typeof UsageBreakdownView>

export const ByRequestType: Story = {
  args: {
    dimension: 'request-type',
    rows: [
      {
        key: 'environment_document',
        label: 'Environment Document',
        value: 5_240_000,
      },
      {
        key: 'identities',
        label: 'Identities',
        value: 1_910_000,
      },
      { key: 'flags', label: 'Flags', value: 730_000 },
      { key: 'traits', label: 'Traits', value: 120_000 },
    ],
  },
}

/** One row dwarfing the rest is the common shape, so the bars must still read. */
export const OneDominantRow: Story = {
  args: {
    dimension: 'request-type',
    rows: [
      { key: 'flags', label: 'Flags', value: 8_900_000 },
      { key: 'identities', label: 'Identities', value: 41_000 },
      { key: 'traits', label: 'Traits', value: 9_000 },
    ],
  },
}

export const BySdk: Story = {
  args: {
    dimension: 'sdk',
    rows: [
      {
        key: 'flagsmith-python-3-9-1',
        label: 'flagsmith-python/3.9.1',
        value: 3_100_000,
      },
      {
        key: 'flagsmith-java-7-2-0',
        label: 'flagsmith-java/7.2.0',
        value: 2_450_000,
      },
      {
        key: 'flagsmith-nodejs-5-0-4',
        label: 'flagsmith-nodejs/5.0.4',
        value: 980_000,
      },
      { key: 'unknown', label: 'Unknown', value: 210_000 },
    ],
  },
}

export const ByProject: Story = {
  args: {
    dimension: 'project',
    rows: [
      { key: 'checkout', label: 'Checkout', value: 4_120_000 },
      { key: 'mobile-app', label: 'Mobile app', value: 2_060_000 },
      { key: 'internal-tools', label: 'Internal tools', value: 88_000 },
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
