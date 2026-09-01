import type { Meta, StoryObj } from 'storybook'
import UsageOverTime from 'components/pages/usage/components/UsageOverTime'
import { Res } from 'common/types/responses'

const meta: Meta<typeof UsageOverTime> = {
  args: { periodLabel: 'Current billing period' },
  component: UsageOverTime,
  parameters: { layout: 'padded' },
  title: 'Pages/Usage Dashboard/Components/UsageOverTime',
}
export default meta

type Story = StoryObj<typeof UsageOverTime>

// Weekends lighter, so the shape reads like real traffic rather than a ramp.
const DAY_WEIGHTS = [1.08, 1.12, 1.05, 1.1, 0.98, 0.62, 0.58]

const usage = (days: number, perDay: number): Res['organisationUsage'] => {
  const events = Array.from({ length: days }).map((_, index) => {
    const weight = DAY_WEIGHTS[index % DAY_WEIGHTS.length]
    return {
      day: `2026-08-${`${index + 1}`.padStart(2, '0')}`,
      environment_document: Math.round(perDay * weight * 0.04),
      flags: Math.round(perDay * weight * 0.63),
      identities: Math.round(perDay * weight * 0.24),
      labels: { user_agent: null },
      traits: Math.round(perDay * weight * 0.09),
    }
  })
  const sum = (key: keyof (typeof events)[number]) =>
    events.reduce((acc, event) => acc + Number(event[key] ?? 0), 0)

  return {
    events_list: events,
    totals: {
      environmentDocument: sum('environment_document'),
      flags: sum('flags'),
      identities: sum('identities'),
      total:
        sum('flags') +
        sum('identities') +
        sum('traits') +
        sum('environment_document'),
      traits: sum('traits'),
    },
  }
}

export const CumulativeUnderTheCeiling: Story = {
  args: {
    data: usage(18, 70000),
    isBillingPeriod: true,
    limit: 2000000,
  },
}

export const CumulativeCrossingTheCeiling: Story = {
  args: {
    data: usage(24, 110000),
    isBillingPeriod: true,
    limit: 2000000,
  },
}

// A rolling window's total falls as old days drop out, so it gets daily volume
// rather than a line that only ever climbs.
export const DailyVolumeOnARollingWindow: Story = {
  args: {
    data: usage(30, 2000),
    isBillingPeriod: false,
    limit: 50000,
    periodLabel: 'Last 30 days',
  },
}

export const NoLimitToDrawAgainst: Story = {
  args: {
    data: usage(18, 70000),
    isBillingPeriod: true,
    limit: null,
  },
}

export const NoUsageRecorded: Story = {
  args: {
    data: usage(0, 0),
    isBillingPeriod: true,
    limit: 2000000,
  },
}
