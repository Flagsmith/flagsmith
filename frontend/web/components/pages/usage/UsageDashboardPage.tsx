import { FC, useMemo, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import Utils, { planNames } from 'common/utils/utils'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import OverLimitBanner from './components/OverLimitBanner'
import SectionHeading from './components/SectionHeading'
import UsageBreakdown, { useUsageBreakdown } from './components/UsageBreakdown'
import UsageFilters from './components/UsageFilters'
import UsageMeter from './components/UsageMeter'
import UsageOverTime from './components/UsageOverTime'
import UsagePageLayout from './components/UsagePageLayout'
import { useUsageData } from './useUsageData'
import { overLimitNote, overLimitOf } from './overLimit'
import {
  isBilledOnAPeriod,
  isBillingPeriodSelected,
  isChargedForOverages,
  contributionNote,
  planSectionCopy,
  showsContribution,
  showsPlanCeiling,
  periodLabel,
  periodsFor,
  PeriodSelection,
  usageBasisOf,
  resolvePeriod,
} from './utils'

type UsageDashboardPageProps = {
  organisationId: number | undefined
}

const UsageDashboardPage: FC<UsageDashboardPageProps> = ({
  organisationId,
}) => {
  const [project, setProject] = useState<string | undefined>()
  const [projectName, setProjectName] = useState<string | undefined>()
  const selectedProjectId = project ? Number(project) : undefined

  const {
    data: organisation,
    isError: organisationFailed,
    isLoading: loadingOrganisation,
    refetch: refetchOrganisation,
  } = useGetOrganisationQuery(
    organisationId ? { id: organisationId } : skipToken,
  )
  const subscription = organisation?.subscription
  const isFreePlan =
    planNames.free === Utils.getPlanName(subscription?.plan ?? '')
  const basis = usageBasisOf(subscription, isFreePlan)
  const planIsBilled = isBilledOnAPeriod(basis)

  const [chosenPeriod, setChosenPeriod] = useState<PeriodSelection>('default')
  const billingPeriod = resolvePeriod(chosenPeriod, planIsBilled)

  const usage = useUsageData({
    basis,
    organisationId,
    period: billingPeriod,
    projectId: selectedProjectId,
    ready: !!organisation,
  })

  const {
    data: subscriptionMeta,
    isError: limitFailed,
    isLoading: loadingLimit,
    refetch: refetchLimit,
  } = useGetSubscriptionMetadataQuery(
    organisationId ? { id: organisationId } : skipToken,
  )

  const mayBeCharged =
    isBilledOnAPeriod(basis) && isChargedForOverages(subscription)

  const limit = subscriptionMeta?.max_api_calls
  const allowanceTotal = usage.allowance?.totals?.total ?? 0
  // Walks every day in the window to find the crossing, so not per render.
  const exceeded = useMemo(
    () => overLimitOf(allowanceTotal, limit, usage.allowance),
    [allowanceTotal, limit, usage.allowance],
  )

  const periods = periodsFor(planIsBilled)

  const { setDimension, ...breakdown } = useUsageBreakdown({
    data: usage.scoped,
  })

  const selectedPeriod = periodLabel(periods, billingPeriod)

  const scope = [
    selectedProjectId ? projectName : 'All projects',
    selectedPeriod,
  ]
    .filter(Boolean)
    .join(' · ')

  const contribution =
    showsContribution(basis, billingPeriod, selectedProjectId) && projectName
      ? contributionNote(
          projectName,
          usage.scoped?.totals?.total ?? 0,
          allowanceTotal,
        )
      : undefined

  // One line, so being over the limit outranks the project's share.
  const meterNote = exceeded ? overLimitNote(exceeded) : contribution

  if (!organisationId) {
    return null
  }

  return (
    <UsagePageLayout
      isError={organisationFailed || usage.failed || limitFailed}
      isLoading={loadingOrganisation || usage.isLoadingPlan || loadingLimit}
      onRetry={() => {
        refetchOrganisation()
        refetchLimit()
        usage.retry()
      }}
    >
      {exceeded && (
        <OverLimitBanner
          over={exceeded}
          basis={basis}
          canUpgrade={Utils.getFlagsmithHasFeature('payments_enabled')}
          mayBeCharged={mayBeCharged}
          isRestricted={!!organisation?.block_access_to_admin}
        />
      )}

      <SectionHeading {...planSectionCopy(basis, limit)} />

      <UsageMeter total={allowanceTotal} limit={limit} note={meterNote} />

      <SectionHeading
        title='Explore usage'
        hint='Narrow the chart and the breakdown by period or project.'
        action={
          <UsageFilters
            organisationId={organisationId}
            periods={periods}
            period={billingPeriod}
            onChangePeriod={setChosenPeriod}
            projectId={project}
            onChangeProject={(id, name) => {
              setProject(id)
              setProjectName(name)
            }}
          />
        }
      />

      {/* Only the filtered half reloads, so the meter above stays put. */}
      {usage.isLoadingScoped ? (
        <div className='text-center py-5'>
          <Loader />
        </div>
      ) : (
        <>
          <UsageOverTime
            data={usage.scoped}
            limit={
              showsPlanCeiling(billingPeriod, selectedProjectId)
                ? limit
                : undefined
            }
            isBillingPeriod={isBillingPeriodSelected(billingPeriod)}
            periodLabel={selectedPeriod}
          />

          <UsageBreakdown
            {...breakdown}
            onChangeDimension={setDimension}
            scope={scope}
          />
        </>
      )}
    </UsagePageLayout>
  )
}

export default UsageDashboardPage
