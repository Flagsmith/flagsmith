import { FC, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import UsagePageLayout from 'components/pages/usage/components/UsagePageLayout'
import OverLimitBanner from 'components/pages/usage/components/OverLimitBanner'
import SectionHeading from 'components/pages/usage/components/SectionHeading'
import UsageBreakdown, {
  useUsageBreakdown,
} from 'components/pages/usage/components/UsageBreakdown'
import UsageMeter from 'components/pages/usage/components/UsageMeter'
import UsageOverTime from 'components/pages/usage/components/UsageOverTime'
import { overLimitNote, overLimitOf } from 'components/pages/usage/overLimit'
import {
  allowanceWindow,
  contributionNote,
  isBilledOnAPeriod,
  isBillingPeriodSelected,
  isChargedForOverages,
  periodLabel,
  periodsFor,
  PeriodSelection,
  planSectionCopy,
  resolvePeriod,
  showsContribution,
  showsPlanCeiling,
  usageBasisOf,
} from 'components/pages/usage/utils'
import { BillingPeriod, PeriodOption } from 'common/types/requests'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { Subscription } from 'common/types/responses'
import { toUsageResponse, USAGE_SCENARIOS } from './fixtures/usage'
// The harness fakes the project select, so it never renders UsageFilters and
// would otherwise miss the width its stylesheet sets.
import 'components/pages/usage/components/UsageFilters/UsageFilters.scss'

const PROJECTS = [
  'All Projects',
  'Checkout',
  'Mobile app',
  'Internal tools',
  'Marketing site',
]

// Roughly how much of the organisation each project accounts for.
const PROJECT_SHARE: Record<string, number> = {
  'All Projects': 1,
  'Checkout': 0.38,
  'Internal tools': 0.07,
  'Marketing site': 0.13,
  'Mobile app': 0.42,
}

const SCENARIO_FOR: Record<string, keyof typeof USAGE_SCENARIOS> = {
  '90_day_period': 'last90Days',
  current_billing_period: 'currentBillingPeriod',
  previous_billing_period: 'previousBillingPeriod',
  rolling: 'last30Days',
}

const scenarioFor = (period: BillingPeriod, empty: boolean, free: boolean) => {
  if (empty) return []
  if (free) return USAGE_SCENARIOS.freePlan
  return USAGE_SCENARIOS[SCENARIO_FOR[period ?? 'rolling']]
}

const subscriptionOf = (values: Partial<Subscription>): Subscription =>
  ({
    has_active_billing_periods: false,
    payment_method: null,
    plan: 'scale-up',
    ...values,
  } as Subscription)

type HarnessProps = {
  subscription: Subscription
  limit: PlanLimit
  /** Overrides the fixture so the meter reads a chosen percentage. */
  scale?: number
  empty?: boolean
  isLoading?: boolean
  isError?: boolean
  isRestricted?: boolean
}

/**
 * Mirrors what UsageDashboardPage derives, using the real utils rather than a
 * copy of them, so the selects behave here as they do in the app.
 */
const UsagePage: FC<HarnessProps> = ({
  empty,
  isError,
  isLoading,
  isRestricted,
  limit,
  scale = 1,
  subscription,
}) => {
  const isFreePlan = subscription.plan === 'free'
  const basis = usageBasisOf(subscription, isFreePlan)
  const planIsBilled = isBilledOnAPeriod(basis)
  const periods = periodsFor(planIsBilled)

  const [chosenPeriod, setChosenPeriod] = useState<PeriodSelection>('default')
  const [project, setProject] = useState('All Projects')

  const billingPeriod = resolvePeriod(chosenPeriod, planIsBilled)
  const share = PROJECT_SHARE[project] ?? 1
  const filtered = project !== 'All Projects'

  const scoped = toUsageResponse(
    scenarioFor(billingPeriod, !!empty, isFreePlan),
    share * scale,
  )
  const allowance = toUsageResponse(
    scenarioFor(allowanceWindow(basis), !!empty, isFreePlan),
    scale,
  )
  const allowanceTotal = allowance.totals.total
  const exceeded = overLimitOf(allowanceTotal, limit, allowance)

  const contribution = showsContribution(
    basis,
    billingPeriod,
    filtered ? 1 : undefined,
  )
    ? contributionNote(project, scoped.totals.total, allowanceTotal)
    : undefined

  // The note needs the organisation over the period on screen, not over the
  // allowance window, or a project can read as more than all of it.
  const { setDimension, ...breakdown } = useUsageBreakdown({ data: scoped })

  const scope = `${filtered ? project : 'All projects'} · ${periodLabel(
    periods,
    billingPeriod,
  )}`

  return (
    <UsagePageLayout
      isError={isError}
      isLoading={isLoading}
      // Nothing to refetch here; passed so FailedToLoad renders its button.
      onRetry={() => {}}
    >
      {(exceeded || isRestricted) && (
        <OverLimitBanner
          over={exceeded}
          basis={basis}
          canUpgrade
          isRestricted={isRestricted}
          mayBeCharged={
            isBilledOnAPeriod(basis) && isChargedForOverages(subscription)
          }
        />
      )}

      <SectionHeading {...planSectionCopy(basis, limit)} />

      <UsageMeter
        total={allowanceTotal}
        limit={limit}
        note={exceeded ? overLimitNote(exceeded) : contribution}
      />

      <SectionHeading
        title='Explore usage'
        hint='Narrow the chart and the breakdown by period or project.'
        action={
          <Row className='gap-2'>
            <div className='usage-filters__field'>
              <Select
                aria-label='Period'
                onChange={(option: PeriodOption) =>
                  setChosenPeriod(option.value)
                }
                options={periods}
                value={periods.find((option) => option.value === billingPeriod)}
              />
            </div>
            <div className='usage-filters__field'>
              <Select
                aria-label='Project'
                onChange={(option: { value: string }) =>
                  setProject(option.value)
                }
                options={PROJECTS.map((name) => ({ label: name, value: name }))}
                value={{ label: project, value: project }}
              />
            </div>
          </Row>
        }
      />

      <UsageOverTime
        data={scoped}
        limit={
          showsPlanCeiling(billingPeriod, filtered ? 1 : undefined)
            ? limit
            : undefined
        }
        isBillingPeriod={isBillingPeriodSelected(billingPeriod)}
        periodLabel={periodLabel(periods, billingPeriod)}
      />

      <UsageBreakdown
        {...breakdown}
        onChangeDimension={setDimension}
        scope={scope}
      />
    </UsagePageLayout>
  )
}

const meta: Meta<typeof UsagePage> = {
  component: UsagePage,
  parameters: { layout: 'fullscreen' },
  title: 'Pages/Usage Dashboard/Page',
}
export default meta

type Story = StoryObj<typeof UsagePage>

const billed = subscriptionOf({ has_active_billing_periods: true })

export const PaidWithABillingPeriod: Story = {
  args: { limit: 2000000, subscription: billed },
}

export const PaidApproachingTheLimit: Story = {
  args: { limit: 1400000, subscription: billed },
}

// Billed on a term, so the banner mentions charges.
export const PaidOverTheLimit: Story = {
  args: { limit: 900000, subscription: billed },
}

// Already cut off. Only free plans are ever restricted, and this is the page
// they are sent to, so the banner says what gets access back.
export const FreeAndRestricted: Story = {
  args: {
    isRestricted: true,
    limit: 50000,
    subscription: subscriptionOf({ plan: 'free' }),
  },
}

// The block outlives the overage: usage is back under the limit but access
// has not returned yet, which is most of that 30 day window.
export const RestrictedButBackUnderTheLimit: Story = {
  args: {
    isRestricted: true,
    limit: 5000000,
    subscription: subscriptionOf({ plan: 'free' }),
  },
}

export const FreeOnARollingWindow: Story = {
  args: { limit: 50000, subscription: subscriptionOf({ plan: 'free' }) },
}

// Enterprise agreements are invoiced outside Chargebee, so they have a real
// limit and no period. The meter works; the chart falls back to daily volume.
export const EnterpriseWithoutABillingPeriod: Story = {
  args: {
    limit: 50000000,
    subscription: subscriptionOf({
      payment_method: 'XERO',
      plan: 'enterprise',
    }),
  },
}

// Invoiced outside Chargebee, so no charge line.
export const EnterpriseOverTheLimit: Story = {
  args: {
    limit: 1000000,
    subscription: subscriptionOf({
      payment_method: 'XERO',
      plan: 'enterprise',
    }),
  },
}

// On Chargebee, but no period has arrived. Reads differently from invoiced,
// because this one may resolve itself.
export const ChargebeeWithoutAPeriodYet: Story = {
  args: {
    limit: 2000000,
    subscription: subscriptionOf({ payment_method: 'CHARGEBEE' }),
  },
}

// Self-hosted has no subscription data at all, so nothing to be a percentage of.
export const WithoutAPlanLimit: Story = {
  args: { limit: null, subscription: subscriptionOf({ plan: 'enterprise' }) },
}

export const NoUsageYet: Story = {
  args: { empty: true, limit: 2000000, subscription: billed },
}

export const Loading: Story = {
  args: { isLoading: true, limit: 2000000, subscription: billed },
}

export const FailedToLoad: Story = {
  args: { isError: true, limit: 2000000, subscription: billed },
}
