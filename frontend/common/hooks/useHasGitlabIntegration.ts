import { useGetGitlabIntegrationQuery } from 'common/services/useGitlabIntegration'

export function useHasGitlabIntegration(projectId: number) {
  const { data } = useGetGitlabIntegrationQuery(
    { project_id: projectId },
    { skip: !projectId },
  )

  return {
    hasIntegration: !!data?.results?.length,
  }
}
