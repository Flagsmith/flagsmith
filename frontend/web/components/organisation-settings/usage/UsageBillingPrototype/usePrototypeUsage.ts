import { useEffect, useMemo, useState } from 'react'
import moment from 'moment'
import { OrganisationUsageNotification, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { useGetOrganisationUsageNotificationsQuery } from 'common/services/useOrganisationUsageNotification'
import {
  organisationUsageService,
  useGetOrganisationUsageQuery,
} from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { getStore } from 'common/store'
import { FIXTURES, ScenarioId } from './fixtures'
import {
  BreakdownDimension,
  BreakdownRow,
  USAGE_ALERT_THRESHOLDS,
  UsageView,
} from './types'

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
  /** Only the visible dimension is fetched, since each one costs N requests. */
  dimension: BreakdownDimension
}

type UsageKey = { label: string; args: Partial<Req['getOrganisationUsage']> }

/**
 * usage-data takes project_id and environment_id as filters rather than as a
 * grouping, so a breakdown is one request per key, summed here. A group_by on
 * the endpoint would make this a single call.
 */
const useKeyedUsage = (
  keys: UsageKey[],
  organisationId: number,
  billingPeriod: Req['getOrganisationUsage']['billing_period'],
  enabled: boolean,
): BreakdownRow[] => {
  const [rows, setRows] = useState<BreakdownRow[]>([])
  // Keys come from a query result, so a new array identity arrives on every
  // render. Compare by content to avoid refetching in a loop.
  const signature = JSON.stringify(keys)

  useEffect(() => {
    if (!enabled || !keys.length) {
      setRows([])
      return
    }
    let cancelled = false
    Promise.all(
      keys.map((key) =>
        getStore()
          .dispatch(
            organisationUsageService.endpoints.getOrganisationUsage.initiate({
              billing_period: billingPeriod,
              organisationId,
              ...key.args,
            }),
          )
          .unwrap()
          .then((res) => ({
            label: key.label,
            value: res?.totals?.total ?? 0,
          }))
          .catch(() => ({ label: key.label, value: 0 })),
      ),
    ).then((result) => {
      if (cancelled) return
      setRows(
        result.filter((row) => row.value > 0).sort((a, b) => b.value - a.value),
      )
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, organisationId, billingPeriod, enabled])

  return rows
}

/**
 * What the usage notifications tell us about being over the limit.
 *
 * The endpoint returns the threshold crossings inside the current period, so
 * the earliest one at or above 100% is when this organisation went over, and
 * the free grace window runs 7 days from it.
 */
const GRACE_DAYS = 7

const readOverLimit = (
  notifications: OrganisationUsageNotification[] | undefined,
) => {
  const overLimit = (notifications ?? [])
    .filter((notification) => notification.percent_usage >= 100)
    .sort((a, b) => (a.notified_at < b.notified_at ? -1 : 1))

  const first = overLimit[0]
  if (!first) {
    return {}
  }

  const since = moment(first.notified_at)
  const daysOverLimit = Math.max(0, moment().diff(since, 'days'))

  return {
    daysOverLimit: daysOverLimit || undefined,
    graceDaysLeft: Math.max(0, GRACE_DAYS - daysOverLimit) || undefined,
    overLimitSince: since.format('D MMM'),
  }
}

const buildLiveView = (
  usage: Res['organisationUsage'] | undefined,
  breakdownUsage: Res['organisationUsage'] | undefined,
  limit: number | null,
  isOnFreePlanPeriods: boolean,
  notifications: OrganisationUsageNotification[] | undefined,
): UsageView => {
  const overLimit = readOverLimit(notifications)
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

  const source = breakdownUsage ?? usage
  const totals = source?.totals

  // Every event row carries the SDK that made the call, so this dimension is a
  // grouping of the response we already have rather than another request.
  const bySdk = new Map<string, number>()
  for (const event of source?.events_list ?? []) {
    const key = event.labels?.user_agent || 'Unknown'
    bySdk.set(
      key,
      (bySdk.get(key) ?? 0) +
        (event.flags ?? 0) +
        (event.identities ?? 0) +
        (event.traits ?? 0) +
        (event.environment_document ?? 0),
    )
  }

  return {
    breakdowns: {
      // Project and environment exist on usage-data as filters, not as a
      // grouping, so they need one request per key or a group_by parameter.
      // Neither is worth doing in the prototype. See the epic.
      environment: [],
      project: [],
      'request-type': [
        {
          label: 'Flag evaluations',
          op: 'get-flags',
          value: totals?.flags ?? 0,
        },
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
      sdk: [...bySdk.entries()]
        .map(([label, value]) => ({ label, value }))
        .sort((a, b) => b.value - a.value),
    },
    channels: { email: true, inApp: true },
    ...overLimit,
    // Whether grace has already been spent is still not exposed, so an
    // organisation that is over the limit is shown the countdown rather than
    // the "grace already used" case. See #8256.
    grace: overLimit.daysOverLimit ? 'countdown' : 'available',
    limit,
    notifications: USAGE_ALERT_THRESHOLDS.map((percent) => ({
      enabled: true,
      percent,
    })),
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
      selectValue: isOnFreePlanPeriods ? undefined : 'current_billing_period',
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
  dimension,
  isOnFreePlanPeriods,
  organisationId,
  projectId,
  scenario,
}: Params): UsageView => {
  const isLive = scenario === 'live'
  const wantsProjects = isLive && dimension === 'project'
  // Environments belong to projects, so without one selected this would fan
  // out to every project times every environment. The panel asks for a project
  // instead.
  const wantsEnvironments = isLive && dimension === 'environment' && !!projectId

  const { data: projects } = useGetProjectsQuery(
    { organisationId },
    { skip: !organisationId || !wantsProjects },
  )
  const { data: environments } = useGetEnvironmentsQuery(
    { projectId: projectId ?? 0 },
    { skip: !projectId || !wantsEnvironments },
  )

  const projectKeys = useMemo<UsageKey[]>(
    () =>
      (projects ?? []).map((project) => ({
        args: { projectId: project.id },
        label: project.name,
      })),
    [projects],
  )
  const environmentKeys = useMemo<UsageKey[]>(
    () =>
      (environments?.results ?? []).map((environment) => ({
        args: { environmentId: `${environment.id}`, projectId },
        label: environment.name,
      })),
    [environments, projectId],
  )

  const projectRows = useKeyedUsage(
    projectKeys,
    organisationId,
    billingPeriod,
    wantsProjects,
  )
  const environmentRows = useKeyedUsage(
    environmentKeys,
    organisationId,
    billingPeriod,
    wantsEnvironments,
  )

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
  const { data: notifications } = useGetOrganisationUsageNotificationsQuery(
    { organisationId },
    { skip: !organisationId || !isLive },
  )

  return useMemo(() => {
    if (!isLive) {
      return FIXTURES[scenario]
    }
    const view = buildLiveView(
      orgUsage,
      filteredUsage,
      subscriptionMeta?.max_api_calls ?? null,
      isOnFreePlanPeriods,
      notifications?.results,
    )
    return {
      ...view,
      breakdowns: {
        ...view.breakdowns,
        environment: environmentRows,
        project: projectRows,
      },
    }
  }, [
    isLive,
    scenario,
    orgUsage,
    filteredUsage,
    subscriptionMeta,
    isOnFreePlanPeriods,
    projectRows,
    environmentRows,
    notifications,
  ])
}

export default usePrototypeUsage
