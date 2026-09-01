import { FC, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import Utils, { planNames } from 'common/utils/utils'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import ProjectFilter from 'components/ProjectFilter'
import { PeriodOption } from 'common/types/requests'
import UsageBreakdown, { useUsageBreakdown } from './components/UsageBreakdown'
import UsageDashboard from './UsageDashboard'
import { useUsageData } from './useUsageData'
import { overLimitNote, overLimitOf } from './overLimit'
import {
  isBilledOnAPeriod,
  isBillingPeriodSelected,
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
import './UsageDashboardPage.scss'

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

  const limit = subscriptionMeta?.max_api_calls
  const allowanceTotal = usage.allowance?.totals?.total ?? 0
  const exceeded = overLimitOf(allowanceTotal, limit, usage.allowance)

  const periods = periodsFor(planIsBilled)

  const { setDimension, ...breakdown } = useUsageBreakdown({
    data: usage.scoped,
  })

  const scope = [
    selectedProjectId ? projectName : 'All projects',
    periodLabel(periods, billingPeriod),
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

  // Being over the limit outranks the project's share of usage: the slot holds
  // one line and only one of them is urgent.
  const meterNote = exceeded ? overLimitNote(exceeded) : contribution

  if (!organisationId) {
    return null
  }

  return (
    <UsageDashboard
      data={usage.scoped}
      total={allowanceTotal}
      limit={limit}
      hasBillingPeriod={isBillingPeriodSelected(billingPeriod)}
      planCopy={planSectionCopy(basis, limit)}
      periodLabel={periodLabel(periods, billingPeriod)}
      showPlanCeiling={showsPlanCeiling(billingPeriod, selectedProjectId)}
      meterNote={meterNote}
      breakdown={
        <UsageBreakdown
          {...breakdown}
          onChangeDimension={setDimension}
          scope={scope}
        />
      }
      isError={organisationFailed || usage.failed || limitFailed}
      isLoading={loadingOrganisation || usage.isLoadingPlan || loadingLimit}
      isExploring={usage.isLoadingScoped}
      // Restriction only ever applies to a free plan, so a paid organisation
      // over its limit keeps serving flags and this only reports the overage.
      overLimit={
        exceeded
          ? {
              basis,
              canUpgrade: Utils.getFlagsmithHasFeature('payments_enabled'),
              over: exceeded,
            }
          : undefined
      }
      onRetry={() => {
        refetchOrganisation()
        refetchLimit()
        usage.retry()
      }}
      filters={
        <Row className='gap-2'>
          <div className='usage-dashboard__filter'>
            <Select
              aria-label='Period'
              inputId='usage-period'
              onChange={(option: PeriodOption) => setChosenPeriod(option.value)}
              value={periods.find((period) => period.value === billingPeriod)}
              options={periods}
            />
          </div>
          <div className='usage-dashboard__filter'>
            <ProjectFilter
              aria-label='Project'
              inputId='usage-project'
              showAll
              organisationId={organisationId}
              onChange={(id: string, name: string) => {
                setProject(id)
                setProjectName(name)
              }}
              value={project}
            />
          </div>
        </Row>
      }
    />
  )
}

export default UsageDashboardPage
