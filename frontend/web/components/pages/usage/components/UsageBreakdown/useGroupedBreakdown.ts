import { useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { BillingPeriod } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import {
  breakdownStatusOf,
  byScope,
  BreakdownDimension,
  BreakdownRow,
  BreakdownStatus,
  groupByOf,
  isGroupedDimension,
} from './utils'

type UseGroupedBreakdown = {
  dimension: BreakdownDimension
  organisationId: number
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
}: UseGroupedBreakdown): GroupedBreakdown | undefined => {
  const groupBy = groupByOf(dimension, projectId)

  // currentData, so a dimension never shows the rows of the one before it.
  const grouped = useGetOrganisationUsageQuery(
    groupBy
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
    groupBy === 'project' ? { organisationId } : skipToken,
  )
  const environments = useGetEnvironmentsQuery(
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
        new Map(
          environments.currentData?.results.map(({ id, name }) => [id, name]),
        ),
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

  if (!isGroupedDimension(dimension)) {
    return undefined
  }

  const queries = [grouped, projects, environments]

  return {
    onRetry: () =>
      queries.forEach((query) => {
        if (!query.isUninitialized) query.refetch()
      }),
    rows,
    status: breakdownStatusOf(groupBy, queries),
  }
}
