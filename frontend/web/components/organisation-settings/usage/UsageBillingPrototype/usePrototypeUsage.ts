import { useMemo } from 'react'
import moment from 'moment'
import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import { FIXTURES, ScenarioId } from './fixtures'
import { UsageView } from './types'

/**
 * PROTOTYPE (#8184). The one place the page gets its data.
 *
 * Either a fixture or the live endpoints, mapped to the same view model. When
 * the real endpoints land, the fixture branch goes and the live branch keeps
 * its shape, so the page itself does not change.
 */

type Params = {
  scenario: ScenarioId
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  projectId?: number
  isOnFreePlanPeriods: boolean
}

const buildLiveView = (
  usage: Res['organisationUsage'] | undefined,
  breakdownUsage: Res['organisationUsage'] | undefined,
  limit: number | null,
  isOnFreePlanPeriods: boolean,
): UsageView => {
  const events = [...(usage?.events_list ?? [])].sort((a, b) =>
    a.day < b.day ? -1 : 1,
  )
  let running = 0
  const series = events.map((event) => {
    running +=
      (event.flags ?? 0) +
      (event.identities ?? 0) +
      (event.traits ?? 0) +
      (event.environment_document ?? 0)
    return { cumulative: running, day: event.day }
  })

  const totals = (breakdownUsage ?? usage)?.totals

  return {
    breakdown: [
      { label: 'Flag evaluations', op: 'get-flags', value: totals?.flags ?? 0 },
      {
        label: 'Identity flag evaluations',
        op: 'get-identity-flags',
        value: totals?.identities ?? 0,
      },
      {
        label: 'Trait updates',
        op: 'set-identity-traits',
        value: totals?.traits ?? 0,
      },
      {
        label: 'Environment bootstrap',
        op: 'get-environment-document',
        value: totals?.environmentDocument ?? 0,
      },
    ],
    channels: { email: true, inApp: true },
    // Grace state is not serialised by the API yet (see the epic), so live
    // data can only ever show the neutral case.
    grace: 'available',
    limit,
    notifications: [
      { enabled: true, percent: 75 },
      { enabled: true, percent: 100 },
    ],
    // Needs per-org pricing, which is not queryable yet.
    overageCost: null,
    period: {
      daysRemaining: 0,
      isBillingPeriod: !isOnFreePlanPeriods,
      // The reset date needs the billing term boundaries, which the API does
      // not return with usage data yet.
      label: events.length
        ? `${moment(events[0].day).format('D MMM')} to ${moment(
            events[events.length - 1].day,
          ).format('D MMM YYYY')}`
        : 'No usage recorded',
      resetsAt: '',
    },
    plan: isOnFreePlanPeriods ? 'free' : 'paid',
    projected: null,
    restricted: false,
    series,
    total: usage?.totals?.total ?? 0,
  }
}

const usePrototypeUsage = ({
  billingPeriod,
  isOnFreePlanPeriods,
  organisationId,
  projectId,
  scenario,
}: Params): UsageView => {
  const isLive = scenario === 'live'

  const { data: orgUsage } = useGetOrganisationUsageQuery(
    { billing_period: billingPeriod, organisationId },
    { skip: !organisationId || !isLive },
  )
  const { data: filteredUsage } = useGetOrganisationUsageQuery(
    { billing_period: billingPeriod, organisationId, projectId },
    { skip: !organisationId || !isLive },
  )
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery(
    { id: organisationId },
    { skip: !organisationId || !isLive },
  )

  return useMemo(() => {
    if (!isLive) {
      return FIXTURES[scenario]
    }
    return buildLiveView(
      orgUsage,
      filteredUsage,
      subscriptionMeta?.max_api_calls ?? null,
      isOnFreePlanPeriods,
    )
  }, [
    isLive,
    scenario,
    orgUsage,
    filteredUsage,
    subscriptionMeta,
    isOnFreePlanPeriods,
  ])
}

export default usePrototypeUsage
