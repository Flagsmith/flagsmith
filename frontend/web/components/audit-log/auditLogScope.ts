type Named = { name: string } | null

// Members, roles and groups: nothing below the organisation.
export const isOrganisationEvent = (item: {
  project: Named
  environment: Named
}): boolean => !item.project && !item.environment

export const getAuditLogScopeLabel = (item: {
  project: Named
  environment: Named
}): string | null => {
  const { environment, project } = item
  if (isOrganisationEvent(item)) return 'Organisation'
  if (!project) return environment?.name ?? null
  return environment ? `${project.name} · ${environment.name}` : project.name
}
