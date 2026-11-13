import type { Environment } from 'common/types/responses'

export function getProjectLandingPath(
  projectId: number,
  environmentsByName: Environment[],
): string {
  const environment = environmentsByName[0]
  return environment
    ? `/project/${projectId}/environment/${environment.api_key}/features`
    : `/project/${projectId}/environment/create`
}
