import { useMemo, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { UsageScope } from './components/ScopeTotal'
import { useScopedBreakdown } from './useScopedBreakdown'
import { byRequestType, bySdk, BreakdownDimension } from './utils'

type UseUsageBreakdown = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  /** Already fetched for the charts above, so request type and SDK are free. */
  data: Res['organisationUsage'] | undefined
  /** The page's project filter. Environments can only be listed under one. */
  projectId: number | undefined
}

/** Keeps the queries out of the section, so it renders from props alone. */
export const useUsageBreakdown = ({
  billingPeriod,
  data,
  organisationId,
  projectId,
}: UseUsageBreakdown) => {
  const [dimension, setDimension] = useState<BreakdownDimension>('request-type')

  // currentData rather than data: RTK keeps the previous result when the
  // arguments change, so a project switch would briefly list the old project's
  // environments while the new request is still out.
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
        environmentId: environment.api_key,
        key: `environment-${environment.api_key}`,
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
    // Until the keys are known there are no scopes to wait on, so without this
    // switching dimension shows "no usage" before the first request is made.
    isLoading: loadingProjects || loadingEnvironments || scoped.isLoading,
    needsProject: dimension === 'environment' && !projectId,
    onTotal: scoped.onTotal,
    rows,
    scopes,
    setDimension,
  }
}
