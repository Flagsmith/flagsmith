export type AuditLogScopeFilter =
  | { type: 'all' }
  | { type: 'organisation' }
  | { type: 'project'; projectId: number; environmentIds: number[] }

const toIds = (values: string[]) => [
  ...new Set(values.map(Number).filter((n) => Number.isInteger(n) && n > 0)),
]

export const parseScope = (params: URLSearchParams): AuditLogScopeFilter => {
  const [projectId] = toIds(params.getAll('project'))
  if (projectId) {
    return {
      environmentIds: toIds(params.getAll('environment')),
      projectId,
      type: 'project',
    }
  }
  return params.get('scope') === 'organisation'
    ? { type: 'organisation' }
    : { type: 'all' }
}

export const writeScopeParams = (
  params: URLSearchParams,
  scope: AuditLogScopeFilter,
) => {
  params.delete('scope')
  params.delete('project')
  params.delete('environment')
  if (scope.type === 'organisation') params.set('scope', 'organisation')
  if (scope.type === 'project') {
    params.set('project', `${scope.projectId}`)
    scope.environmentIds.forEach((id) => params.append('environment', `${id}`))
  }
}

export const getScopeDisplayLabel = (
  scope: AuditLogScopeFilter,
  projectName: string | undefined,
): string => {
  if (scope.type === 'organisation') return 'Organisation'
  if (scope.type === 'all') return 'Everything'
  const name = projectName ?? 'Project'
  const count = scope.environmentIds.length
  if (!count) return name
  return `${name} · ${count} ${count === 1 ? 'environment' : 'environments'}`
}
