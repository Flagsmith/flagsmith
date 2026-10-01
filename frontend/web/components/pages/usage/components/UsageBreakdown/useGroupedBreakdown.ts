import { useMemo } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { BillingPeriod, UsageGroupBy } from 'common/types/requests'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { byScope, BreakdownDimension, BreakdownRow } from './utils'

type UseGroupedBreakdown = {
  dimension: BreakdownDimension
  organisationId: number
  billingPeriod: BillingPeriod
  projectId: number | undefined
}

export type GroupedBreakdown = {
  rows: BreakdownRow[]
  isLoading: boolean
  isError: boolean
  needsProject: boolean
  onRetry: () => void
}

const groupByOf = (
  dimension: BreakdownDimension,
  projectId: number | undefined,
): UsageGroupBy | undefined => {
  if (dimension === 'project') return 'project'
  // Environments are only ranked within one project.
  if (dimension === 'environment' && projectId) return 'environment'
  return undefined
}

// Project and environment need their own grouped request; request type and
// SDK come from the rows the page already holds.
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

  if (dimension !== 'project' && dimension !== 'environment') {
    return undefined
  }

  return {
    // A failed scope must not read as zero usage.
    isError: grouped.isError || projects.isError || environments.isError,
    isLoading:
      grouped.isFetching || projects.isFetching || environments.isFetching,
    needsProject: !groupBy,
    onRetry: () => {
      if (!grouped.isUninitialized) grouped.refetch()
      if (!projects.isUninitialized) projects.refetch()
      if (!environments.isUninitialized) environments.refetch()
    },
    rows,
  }
}
