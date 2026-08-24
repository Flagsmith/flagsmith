import { FC, useMemo, useState } from 'react'
import { skipToken } from '@reduxjs/toolkit/query'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import UsageBreakdownView from './UsageBreakdownView'
import ScopeTotal, { UsageScope } from './components/ScopeTotal'
import { useScopedBreakdown } from './useScopedBreakdown'
import { byRequestType, bySdk, BreakdownDimension } from './utils'

export type UsageBreakdownProps = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  /** Already fetched for the charts above, so these two cost nothing extra. */
  data: Res['organisationUsage'] | undefined
  /** The page's project filter. Environments can only be listed under one. */
  projectId: number | undefined
}

const UsageBreakdown: FC<UsageBreakdownProps> = ({
  billingPeriod,
  data,
  organisationId,
  projectId,
}) => {
  const [dimension, setDimension] = useState<BreakdownDimension>('request-type')

  const { data: projects, isLoading: loadingProjects } = useGetProjectsQuery(
    dimension === 'project' ? { organisationId } : skipToken,
  )
  const { data: environments, isLoading: loadingEnvironments } =
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
    `${dimension}|${billingPeriod ?? 'rolling'}|${projectId ?? 'all'}`,
  )

  const rows = useMemo(() => {
    if (dimension === 'request-type') return byRequestType(data)
    if (dimension === 'sdk') return bySdk(data)
    return scoped.rows
  }, [dimension, data, scoped.rows])

  const needsProject = dimension === 'environment' && !projectId

  // Until the keys are known there are no scopes to wait on, so without this
  // switching dimension shows "no usage" before the first request is even made.
  const loadingScopes = loadingProjects || loadingEnvironments

  return (
    <>
      {!needsProject &&
        scopes.map((scope) => (
          <ScopeTotal
            key={scope.key}
            organisationId={organisationId}
            billingPeriod={billingPeriod}
            scope={scope}
            onTotal={scoped.onTotal}
          />
        ))}

      <UsageBreakdownView
        dimension={dimension}
        onChangeDimension={setDimension}
        rows={rows}
        isLoading={loadingScopes || scoped.isLoading}
        needsProject={needsProject}
      />
    </>
  )
}

export default UsageBreakdown
