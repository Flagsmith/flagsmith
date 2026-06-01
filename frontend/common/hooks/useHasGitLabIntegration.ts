import { useGetGitLabConfigurationQuery } from 'common/services/useGitlabConfiguration'

export function useHasGitLabIntegration(projectId: number) {
  const { data } = useGetGitLabConfigurationQuery(
    { project_id: projectId },
    { skip: !projectId },
  )
  return { hasIntegration: !!data?.length }
}
