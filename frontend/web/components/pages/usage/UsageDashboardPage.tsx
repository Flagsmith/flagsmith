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
import {
  isBilledOnAPeriod,
  isBillingPeriodSelected,
  contributionNote,
  planSectionCopy,
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

  if (!organisationId) {
    return null
  }

  return (
    <UsageDashboard
      data={usage.scoped}
      total={usage.allowanceTotal}
      limit={subscriptionMeta?.max_api_calls}
      hasBillingPeriod={isBillingPeriodSelected(billingPeriod)}
      planCopy={planSectionCopy(basis, subscriptionMeta?.max_api_calls)}
      periodLabel={periodLabel(periods, billingPeriod)}
      showPlanCeiling={showsPlanCeiling(billingPeriod, selectedProjectId)}
      meterNote={
        selectedProjectId && projectName
          ? contributionNote(
              projectName,
              usage.scoped?.totals?.total ?? 0,
              usage.periodTotal,
            )
          : undefined
      }
      breakdown={
        <UsageBreakdown
          {...breakdown}
          onChangeDimension={setDimension}
          scope={scope}
        />
      }
      isError={organisationFailed || usage.scopedFailed || limitFailed}
      isLoading={loadingOrganisation || usage.isLoadingPlan || loadingLimit}
      isExploring={usage.isLoadingScoped}
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
