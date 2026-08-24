import type { Meta, StoryObj } from 'storybook'
import { UsageDashboard } from 'components/pages/usage'
import { Res } from 'common/types/responses'

const meta: Meta<typeof UsageDashboard> = {
  component: UsageDashboard,
  parameters: { layout: 'fullscreen' },
  title: 'Pages/Usage Dashboard/Page',
}
export default meta

type Story = StoryObj<typeof UsageDashboard>

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
  const sum = (
    key: 'flags' | 'identities' | 'traits' | 'environment_document',
  ) => events.reduce((acc, event) => acc + event[key], 0)

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

const paid = usage(18, 70000)
const free = usage(30, 1800)
const paidApproaching = usage(26, 75000)
const paidOver = usage(28, 92000)

// A plan with a billing term: usage climbs towards a reset, so it is drawn
// cumulatively against the ceiling.
export const PaidWithABillingPeriod: Story = {
  args: {
    data: paid,
    hasBillingPeriod: true,
    limit: 2000000,
    total: paid.totals.total,
  },
}

export const PaidApproachingTheLimit: Story = {
  args: {
    data: paidApproaching,
    hasBillingPeriod: true,
    limit: 2000000,
    total: paidApproaching.totals.total,
  },
}

export const PaidOverTheLimit: Story = {
  args: {
    data: paidOver,
    hasBillingPeriod: true,
    limit: 2000000,
    total: paidOver.totals.total,
  },
}

// No billing term, so no reset to accumulate towards: daily volume instead.
export const FreeOnARollingWindow: Story = {
  args: {
    data: free,
    hasBillingPeriod: false,
    limit: 50000,
    total: free.totals.total,
  },
}

// Enterprise agreements are not billed through Chargebee, so they have a real
// limit and no period. The meter still works; the chart falls back to volume.
export const EnterpriseWithoutABillingPeriod: Story = {
  args: {
    data: paid,
    hasBillingPeriod: false,
    limit: 50000000,
    total: paid.totals.total,
  },
}

// Self-hosted has no subscription data at all, so there is nothing to be a
// percentage of.
export const WithoutAPlanLimit: Story = {
  args: {
    data: paid,
    hasBillingPeriod: false,
    limit: null,
    total: paid.totals.total,
  },
}

export const NoUsageYet: Story = {
  args: {
    data: usage(0, 0),
    hasBillingPeriod: true,
    limit: 2000000,
    total: 0,
  },
}

export const Loading: Story = {
  args: {
    hasBillingPeriod: true,
    isLoading: true,
    limit: 2000000,
    total: 0,
  },
}

/** Distinct from NoUsageYet, which would otherwise look identical. */
export const FailedToLoad: Story = {
  args: {
    hasBillingPeriod: true,
    isError: true,
    limit: 2000000,
    total: 0,
  },
}
