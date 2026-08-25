import { useMemo, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useScopedBreakdown } from './useScopedBreakdown'
import { byRequestType, bySdk, BreakdownDimension, UsageScope } from './utils'

type UseUsageBreakdown = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  data: Res['organisationUsage'] | undefined
  projectId: number | undefined
}

export const useUsageBreakdown = ({
  billingPeriod,
  data,
  organisationId,
  projectId,
}: UseUsageBreakdown) => {
  const [dimension, setDimension] = useState<BreakdownDimension>('request-type')

  const { currentData: projects, isFetching: loadingProjects } =
    useGetProjectsQuery(
      dimension === 'project' ? { organisationId } : skipToken,
    )
  const { currentData: environments, isFetching: loadingEnvironments } =
    useGetEnvironmentsQuery(
      dimension === 'environment' && projectId ? { projectId } : skipToken,
    )

  const scopes: UsageScope[] = useMemo(() => {
    if (dimension === 'project') {
      return (projects ?? []).map((project) => ({
        key: `project-${project.id}`,
        label: project.name,
        projectId: project.id,
      }))
    }
    if (dimension === 'environment') {
      return (environments?.results ?? []).map((environment) => ({
        environmentId: `${environment.id}`,
        key: `environment-${environment.id}`,
        label: environment.name,
      }))
    }
    return []
  }, [dimension, projects, environments])

  const scoped = useScopedBreakdown(
    scopes,
    `${organisationId}|${dimension}|${billingPeriod ?? 'rolling'}|${
      projectId ?? 'all'
    }`,
  )

  const rows = useMemo(() => {
    if (dimension === 'request-type') return byRequestType(data)
    if (dimension === 'sdk') return bySdk(data)
    return scoped.rows
  }, [dimension, data, scoped.rows])

  return {
    dimension,
    isLoading: loadingProjects || loadingEnvironments || scoped.isLoading,
    needsProject: dimension === 'environment' && !projectId,
    onTotal: scoped.onTotal,
    rows,
    scopes,
    setDimension,
  }
}
