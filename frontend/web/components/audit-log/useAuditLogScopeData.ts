import { skipToken } from '@reduxjs/toolkit/query'
import { useGetProjectsQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { getProjectColourMap } from 'common/utils/paletteColour'
import { AuditLogScopeFilter } from './auditLogScopeFilter'
import {
  ScopeCardEnvironment,
  ScopeCardProject,
  ScopeList,
} from './OrganisationAuditLogFilters/ScopeCard'

export default function useAuditLogScopeData(
  organisationId: number,
  scope: AuditLogScopeFilter,
  enabled: boolean,
) {
  const projects = useGetProjectsQuery(enabled ? { organisationId } : skipToken)
  const environments = useGetEnvironmentsQuery(
    enabled && scope.type === 'project'
      ? { projectId: scope.projectId }
      : skipToken,
  )
  // currentData, so a previous organisation's projects or a previous
  // project's environments never show as loaded.
  const projectItems = projects.currentData
  const projectColours = getProjectColourMap(projectItems ?? [])
  const environmentItems = environments.currentData?.results

  const projectList: ScopeList<ScopeCardProject> = {
    failed: projects.isError,
    items: (projectItems ?? []).map((project) => ({
      colour: projectColours.get(project.id),
      id: project.id,
      name: project.name,
    })),
    loading: projects.isFetching && !projectItems,
  }
  const environmentList: ScopeList<ScopeCardEnvironment> = {
    failed: environments.isError,
    items: environmentItems ?? [],
    loading: environments.isFetching && !environmentItems,
  }

  return { environmentList, projectColours, projectList }
}
