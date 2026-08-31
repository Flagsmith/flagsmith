import { FC, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import Utils, { planNames } from 'common/utils/utils'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import ProjectFilter from 'components/ProjectFilter'
import { PeriodOption } from 'common/types/requests'
import UsageBreakdown, { useUsageBreakdown } from './components/UsageBreakdown'
import UsageDashboard from './UsageDashboard'
import {
  isBilledOnAPeriod,
  isBillingPeriodSelected,
  contributionNote,
  allowanceWindow,
  basisExplanation,
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

  const {
    data,
    isError: usageFailed,
    isFetching: loadingUsage,
    isUninitialized: usageNotStarted,
    refetch: refetchUsage,
  } = useGetOrganisationUsageQuery(
    organisationId && organisation
      ? {
          billing_period: billingPeriod,
          organisationId,
          projectId: selectedProjectId,
        }
      : skipToken,
    // usage-data is throttled at five requests a minute per user, so
    // refetching every time the tab regains focus spends that budget.
    { refetchOnFocus: false },
  )
  const { data: organisationData, isFetching: loadingPlan } =
    useGetOrganisationUsageQuery(
      organisationId && organisation
        ? {
            // The meter answers for the allowance window, not the one on screen.
            billing_period: allowanceWindow(basis),
            organisationId,
          }
        : skipToken,
      // usage-data is throttled at five requests a minute per user, so
      // refetching every time the tab regains focus spends that budget.
      { refetchOnFocus: false },
    )

  // The note compares a project with the organisation over the same period, so
  // it needs the unfiltered total for the period on screen, not the allowance
  // one. With no project chosen the arguments match the query above and RTK
  // serves both from one request.
  const { data: periodData } = useGetOrganisationUsageQuery(
    organisationId && organisation && selectedProjectId
      ? { billing_period: billingPeriod, organisationId }
      : skipToken,
    { refetchOnFocus: false },
  )

  const {
    data: subscriptionMeta,
    isLoading: loadingLimit,
    refetch: refetchLimit,
  } = useGetSubscriptionMetadataQuery(
    organisationId ? { id: organisationId } : skipToken,
  )

  const periods = periodsFor(planIsBilled)

  const { setDimension, ...breakdown } = useUsageBreakdown({ data })

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
      data={data}
      total={organisationData?.totals?.total ?? 0}
      limit={subscriptionMeta?.max_api_calls}
      hasBillingPeriod={isBillingPeriodSelected(billingPeriod)}
      planCopy={planSectionCopy(basis, subscriptionMeta?.max_api_calls)}
      basisExplanation={basisExplanation(basis)}
      periodLabel={periodLabel(periods, billingPeriod)}
      showPlanCeiling={showsPlanCeiling(billingPeriod, selectedProjectId)}
      meterNote={
        selectedProjectId && projectName
          ? contributionNote(
              projectName,
              data?.totals?.total ?? 0,
              periodData?.totals?.total ?? 0,
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
      isError={organisationFailed || usageFailed}
      isLoading={loadingOrganisation || loadingPlan || loadingLimit}
      isExploring={loadingUsage}
      onRetry={() => {
        refetchOrganisation()
        refetchLimit()
        if (!usageNotStarted) {
          refetchUsage()
        }
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
