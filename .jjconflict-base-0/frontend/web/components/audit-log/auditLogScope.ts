type Named = { name: string } | null

// Members, roles and groups: nothing below the organisation.
export const isOrganisationEvent = (item: {
  project: Named
  environment: Named
}): boolean => !item.project && !item.environment

// Environment colours only hold within a project, so the row shows it as text.
export const getAuditLogScopeLabel = (item: {
  project: Named
  environment: Named
}): { name: string; environment?: string } | null => {
  const { environment, project } = item
  if (isOrganisationEvent(item)) return { name: 'Organisation' }
  if (!project) return environment ? { name: environment.name } : null
  return { environment: environment?.name, name: project.name }
}
