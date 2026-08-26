import { FC, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import Utils, { planNames } from 'common/utils/utils'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import FieldLabel from 'components/base/forms/FieldLabel'
import ProjectFilter from 'components/ProjectFilter'
import { PeriodOption } from 'common/types/requests'
import UsageBreakdown, { useUsageBreakdown } from './components/UsageBreakdown'
import UsageDashboard from './UsageDashboard'
import {
  isBillingPeriodSelected,
  periodLabel,
  periodsFor,
  PeriodSelection,
  planHasBillingPeriod,
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
  } = useGetOrganisationQuery(
    organisationId ? { id: organisationId } : skipToken,
  )
  const subscription = organisation?.subscription
  const isFreePlan =
    planNames.free === Utils.getPlanName(subscription?.plan ?? '')
  const planIsBilled = planHasBillingPeriod(subscription, isFreePlan)

  const [chosenPeriod, setChosenPeriod] = useState<PeriodSelection>('default')
  const billingPeriod = resolvePeriod(chosenPeriod, planIsBilled)

  const {
    data,
    isError: usageFailed,
    isFetching: loadingUsage,
  } = useGetOrganisationUsageQuery(
    organisationId && organisation
      ? {
          billing_period: billingPeriod,
          organisationId,
          projectId: selectedProjectId,
        }
      : skipToken,
  )
  const { data: subscriptionMeta, isLoading: loadingLimit } =
    useGetSubscriptionMetadataQuery(
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
      total={data?.totals?.total ?? 0}
      limit={subscriptionMeta?.max_api_calls}
      hasBillingPeriod={isBillingPeriodSelected(billingPeriod)}
      breakdown={
        <UsageBreakdown
          {...breakdown}
          onChangeDimension={setDimension}
          scope={scope}
        />
      }
      isError={organisationFailed || usageFailed}
      isLoading={loadingOrganisation || loadingUsage || loadingLimit}
      filters={
        <Row className='gap-3 align-items-end'>
          <div className='usage-dashboard__filter'>
            <FieldLabel htmlFor='usage-period'>Period</FieldLabel>
            <Select
              inputId='usage-period'
              onChange={(option: PeriodOption) => setChosenPeriod(option.value)}
              value={periods.find((period) => period.value === billingPeriod)}
              options={periods}
            />
          </div>
          <div className='usage-dashboard__filter'>
            <FieldLabel htmlFor='usage-project'>Project</FieldLabel>
            <ProjectFilter
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
