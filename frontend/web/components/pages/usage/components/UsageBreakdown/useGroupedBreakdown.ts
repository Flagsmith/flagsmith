import { useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { BillingPeriod } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetAllEnvironmentsQuery } from 'common/services/useEnvironment'
import { breakdownStatusOf, retryFailed } from './breakdownView'
import {
  byScope,
  BreakdownDimension,
  BreakdownRow,
  BreakdownStatus,
  groupByOf,
} from './utils'

type UseGroupedBreakdown = {
  dimension: BreakdownDimension
  // Undefined until the organisation loads, since its plan picks the period.
  organisationId: number | undefined
  billingPeriod: BillingPeriod
  projectId: number | undefined
}

export type GroupedBreakdown = {
  rows: BreakdownRow[]
  status: BreakdownStatus
  onRetry: () => void
}

export const useGroupedBreakdown = ({
  billingPeriod,
  dimension,
  organisationId,
  projectId,
}: UseGroupedBreakdown): GroupedBreakdown => {
  const groupBy = groupByOf(dimension, projectId)

  // currentData, so a dimension never shows the rows of the one before it.
  const grouped = useGetOrganisationUsageQuery(
    groupBy && organisationId
      ? {
          billing_period: billingPeriod,
          group_by: groupBy,
          organisationId,
          projectId,
        }
      : skipToken,
    { refetchOnFocus: false },
  )
  const projects = useGetProjectsQuery(
    groupBy === 'project' && organisationId ? { organisationId } : skipToken,
  )
  const environments = useGetAllEnvironmentsQuery(
    groupBy === 'environment' && projectId ? { projectId } : skipToken,
  )

  const rows = useMemo(() => {
    if (groupBy === 'project') {
      return byScope(
        grouped.currentData,
        'project_id',
        new Map(projects.currentData?.map(({ id, name }) => [id, name])),
        'Deleted project',
      )
    }
    if (groupBy === 'environment') {
      return byScope(
        grouped.currentData,
        'environment_id',
        new Map(environments.currentData?.map(({ id, name }) => [id, name])),
        'Deleted environment',
      )
    }
    return []
  }, [
    environments.currentData,
    grouped.currentData,
    groupBy,
    projects.currentData,
  ])

  const queries = [grouped, projects, environments]
  const status = breakdownStatusOf(groupBy, queries, !!organisationId)
  const onRetry = () => retryFailed(queries)

  return { onRetry, rows, status }
}
