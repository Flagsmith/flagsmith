import { skipToken } from '@reduxjs/toolkit/query'
import { BillingPeriod } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { allowanceWindow, UsageBasis } from './utils'

type UseUsageData = {
  organisationId: number | undefined
  ready: boolean
  basis: UsageBasis
  period: BillingPeriod
  projectId: number | undefined
}

export type UsageData = {
  /** The period and project on screen. Feeds the chart and the breakdown. */
  scoped: Res['organisationUsage'] | undefined
  /** The organisation over the window its allowance covers. Feeds the meter
   * and the over-limit banner. */
  allowance: Res['organisationUsage'] | undefined
  isLoadingPlan: boolean
  isLoadingScoped: boolean
  failed: boolean
  retry: () => void
}

// usage-data is throttled at five requests a minute per user, so refetching
// every time the tab regains focus spends the budget the page needs.
const OPTIONS = { refetchOnFocus: false }

export const useUsageData = ({
  basis,
  organisationId,
  period,
  projectId,
  ready,
}: UseUsageData): UsageData => {
  const forOrganisation = ready && organisationId ? { organisationId } : null

  const scoped = useGetOrganisationUsageQuery(
    forOrganisation
      ? { ...forOrganisation, billing_period: period, projectId }
      : skipToken,
    OPTIONS,
  )

  const allowance = useGetOrganisationUsageQuery(
    forOrganisation
      ? { ...forOrganisation, billing_period: allowanceWindow(basis) }
      : skipToken,
    OPTIONS,
  )

  return {
    allowance: allowance.data,
    // Either query failing leaves a number missing, so both are fatal.
    failed: scoped.isError || allowance.isError,

    isLoadingPlan: allowance.isFetching,

    isLoadingScoped: scoped.isFetching,

    retry: () => {
      if (!scoped.isUninitialized) scoped.refetch()
      if (!allowance.isUninitialized) allowance.refetch()
    },
    scoped: scoped.data,
  }
}
