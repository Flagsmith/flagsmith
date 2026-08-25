import type { Meta, StoryObj } from 'storybook'
import {
  colorChart1,
  colorChart2,
  colorChart3,
  colorChart4,
} from 'common/theme/tokens'
import UsageBreakdown from 'components/pages/usage/components/UsageBreakdown'

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
      {
        colour: colorChart4,
        key: 'environment_document',
        label: 'Environment Document',
        value: 5_240_000,
      },
      {
        colour: colorChart3,
        key: 'identities',
        label: 'Identities',
        value: 1_910_000,
      },
      { colour: colorChart1, key: 'flags', label: 'Flags', value: 730_000 },
      { colour: colorChart2, key: 'traits', label: 'Traits', value: 120_000 },
    ],
  },
}

/** One row dwarfing the rest is the common shape, so the bars must still read. */
export const OneDominantRow: Story = {
  args: {
    dimension: 'request-type',
    rows: [
      { colour: colorChart1, key: 'flags', label: 'Flags', value: 8_900_000 },
      {
        colour: colorChart3,
        key: 'identities',
        label: 'Identities',
        value: 41_000,
      },
      { colour: colorChart2, key: 'traits', label: 'Traits', value: 9_000 },
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

export const NoUsageRecorded: Story = {
  args: { dimension: 'request-type', rows: [] },
}
